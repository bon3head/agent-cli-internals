#!/usr/bin/env python3
"""C1 PoC: Claude Code permission-rule parser / validator / matcher simulator.

Reconstructed from byte-level evidence in claude 2.1.287 (see ../settings-permissions.md):
- Rule parser  : YWe()  @199006950  (bare | Tool(content); ')' must be final unescaped char)
- Normalization: jn()   (empty or '*' content -> bare tool name)
- Validator   : Twe()  @199006950  (empty/malformed/MCP/uppercase/:*-rules/file-alias warnings/allow-wildcard ban)
- Glob->regex : $8()   @199003774  (**/ -> /(?:.*/)? ; * -> .* ; \\* literal ; trailing " *" optional)
- Bash match  : yt()   @220570938  (exact | prefix (:*) | wildcard; case-insensitive)
- Decision    : Zt()/Le() (deny > ask > allow > passthrough; first match within tier wins)

LIMITATIONS (marked INFERENCE in the doc):
- Executable-basename resolution inside yt() (Sjn/Xy) is environment-dependent; the
  simulator matches the raw command string only.
- File-path rules are matched case-sensitively here; the binary's exact flag for the
  file path is not fully pinned.
- Cross-source tie order within a tier follows _xe merge order
  (user,project,local,flag,policy,cliArg,command,session,...); the simulator takes
  caller-ordered lists.
"""
import re
import sys

# ---------------------------------------------------------------- parser (YWe)

def _first_unescaped(s, ch):
    for i, c in enumerate(s):
        if c == ch:
            bs = 0
            j = i - 1
            while j >= 0 and s[j] == '\\':
                bs += 1
                j -= 1
            if bs % 2 == 0:
                return i
    return -1


def _last_unescaped(s, ch):
    for i in range(len(s) - 1, -1, -1):
        if s[i] == ch:
            bs = 0
            j = i - 1
            while j >= 0 and s[j] == '\\':
                bs += 1
                j -= 1
            if bs % 2 == 0:
                return i
    return -1


def parse_rule(rule):
    """-> dict(kind=bare|call|malformed, toolName, rawContent). Mirrors YWe()."""
    n = _first_unescaped(rule, '(')
    t = _last_unescaped(rule, ')')
    if n == -1 and t == -1:
        return {'kind': 'bare', 'toolName': rule, 'rawContent': None}
    head = rule.substring(0, n) if False else rule[:n]
    if n == -1 or t <= n or t != len(rule) - 1 or re.search(r'[()]', head):
        return {'kind': 'malformed', 'toolName': None, 'rawContent': None}
    return {'kind': 'call', 'toolName': head, 'rawContent': rule[n + 1:t]}


def normalize_rule(rule):
    """Mirrors jn(): empty or '*' content collapses to the bare tool name."""
    p = parse_rule(rule)
    if p['kind'] != 'call' or not p['toolName']:
        return {'toolName': rule.strip(), 'ruleContent': None}
    if p['rawContent'] == '' or p['rawContent'] == '*':
        return {'toolName': p['toolName'], 'ruleContent': None}
    return {'toolName': p['toolName'], 'ruleContent': p['rawContent']}


# ---------------------------------------------------------------- $8 glob -> regex

_ESC_STAR = '\x00ESCAPED_STAR\x00'
_ESC_BS = '\x00ESCAPED_BACKSLASH\x00'
_GLOBSTAR = '\x00GLOBSTAR\x00'


def glob_to_regex(pattern, case_insensitive=False):
    """Mirrors $8(e,n,s,r): glob pattern -> compiled regex. Returns None if never-matches."""
    if '\x00' in pattern:
        return None
    i = pattern.strip()
    # escape processing: \* -> placeholder, \\ -> placeholder
    p = []
    g = 0
    while g < len(i):
        c = i[g]
        if c == '\\' and g + 1 < len(i):
            nxt = i[g + 1]
            if nxt == '*':
                p.append(_ESC_STAR)
                g += 2
                continue
            elif nxt == '\\':
                p.append(_ESC_BS)
                g += 2
                continue
        p.append(c)
        g += 1
    p = ''.join(p)
    s = re.sub(r'[.+?^${}()|[\]\\\'"]', r'\\\g<0>', p)
    s = re.sub(r'/(?:\*/)+', _GLOBSTAR, s)   # jg: / followed by (*/)+ 
    s = s.replace('*', '.*')
    s = s.replace(_GLOBSTAR, '/(?:.*/)?')    # Fg
    s = s.replace(_ESC_STAR, r'\*')          # Hg
    s = s.replace(_ESC_BS, r'\\\\')          # Kg
    stars = p.count('*')
    if s.endswith(' .*') and stars == 1:
        s = s[:-3] + '( .*)?'                # `git *` also matches bare `git`
    flags = re.IGNORECASE if case_insensitive else 0
    return re.compile('^' + s + '$', flags)


def _has_unescaped_star(s):
    for i, c in enumerate(s):
        if c == '*':
            bs = 0
            j = i - 1
            while j >= 0 and s[j] == '\\':
                bs += 1
                j -= 1
            if bs % 2 == 0:
                return True
    return False


def _ends_unescaped_star(s):
    t = s.rstrip()
    if not t.endswith('*'):
        return False
    bs = 0
    j = len(t) - 2
    while j >= 0 and t[j] == '\\':
        bs += 1
        j -= 1
    return bs % 2 == 0


def bash_rule_kind(content):
    """prefix | wildcard | exact — from kwe()/V8r() in the binary."""
    m = re.match(r'^(.+):\*$', content)
    if m:
        return 'prefix', m.group(1)
    if _has_unescaped_star(content):
        return 'wildcard', content
    return 'exact', content


# ---------------------------------------------------------------- validator (Twe)

_MCP_RE = re.compile(r'^mcp__([^_]+)__(.*)$')


def validate_rule(rule, tier='allow'):
    """Mirrors Twe(e, n): -> (ok: bool, problems: [str], warnings: [str])."""
    problems, warnings = [], []
    if not rule or not rule.strip():
        return False, ['Permission rule cannot be empty'], []
    p = parse_rule(rule)
    if p['kind'] == 'malformed':
        return False, ['Malformed Tool(content) rule: rules take the form Tool or Tool(content) '
                        'and must end at the closing ")"; parentheses inside the content are literal'], []
    if p['kind'] == 'call' and p['rawContent'] == '':
        if not p['toolName']:
            return False, ['Empty parentheses with no tool name'], []
        return False, [f'Empty parentheses: either specify a pattern or use just "{p["toolName"]}" '
                       'without parentheses'], []
    n = normalize_rule(rule)
    tool = n['toolName']
    mcp = _MCP_RE.match(tool)
    if mcp:
        if p['kind'] == 'call':
            return False, ['MCP rules do not support patterns in parentheses: use "%s" without '
                           'parentheses, or "mcp__%s__*" for all tools' % (tool, mcp.group(1))], []
        if tier == 'allow' and ('*' in tool):
            # Wbt: globs only allowed in tool position after literal mcp__<server>__ prefix
            if not re.match(r'^mcp__[^_*]+__[^_]*\*?$', tool):
                return False, [f'Wildcard tool name "{tool}" is not supported in allow rules'], []
        return True, [], []
    if not tool:
        return False, ['Tool name cannot be empty'], []
    if tier == 'allow' and '*' in tool:
        return False, [f'Wildcard tool name "{tool}" is not supported in allow rules: an allow pattern '
                       'must name the scope it widens. Deny and ask rules accept wildcards anywhere'], []
    if '_' not in tool and tool[0] != tool[0].upper():
        return False, [f'Tool names must start with uppercase: use "{tool[0].upper() + tool[1:]}"'], []
    content = n['ruleContent']
    if content is not None:
        is_bash = tool in ('Bash', 'PowerShell')
        is_file_tool = tool in ('Edit', 'Read', 'Write', 'NotebookEdit', 'MultiEdit', 'Glob')
        if ':*' in content and not content.endswith(':*'):
            warnings.append(f'{tool}({content}) has a :* that is not at the end, so it is matched as '
                            'a * wildcard (the : is literal), not as the trailing :* prefix syntax')
        if is_file_tool and ':*' in content:
            return False, ['The ":*" syntax is only for Bash prefix rules: use glob patterns like "*" '
                           'or "**" for file matching'], []
        alias = {'Write': 'Edit', 'NotebookEdit': 'Edit', 'MultiEdit': 'Edit', 'Glob': 'Read'}.get(tool)
        if alias and ':*' not in content:
            warnings.append(f'{tool}({content}) is not matched by file permission checks \u2014 only '
                            f'{alias}(path) rules are. Use {alias}({content}) instead')
    return True, problems, warnings


# ---------------------------------------------------------------- matching

def _match_bash(rule_content, command):
    kind, pat = bash_rule_kind(rule_content)
    cmd = command.strip()
    if kind == 'prefix':
        p = pat.strip()
        return cmd.lower() == p.lower() or cmd.lower().startswith(p.lower() + ' ')
    if kind == 'wildcard':
        rx = glob_to_regex(pat, case_insensitive=True)
        return bool(rx and rx.match(cmd))
    return cmd.lower() == pat.strip().lower()


def _match_file(rule_content, path):
    rx = glob_to_regex(rule_content, case_insensitive=False)
    return bool(rx and rx.match(path))


# tool-name -> canonical file-permission tool for path rules (validator warning basis)
_FILE_CANON = {'Write': 'Edit', 'NotebookEdit': 'Edit', 'MultiEdit': 'Edit', 'Glob': 'Read'}


def rule_matches(rule, tool_name, invocation):
    """Does `rule` match a call of tool `tool_name` with `invocation`
    (command string for Bash, path string for file tools)?"""
    n = normalize_rule(rule)
    if n['toolName'] != tool_name:
        return False
    content = n['ruleContent']
    if content is None:
        return True  # bare tool rule matches every call of that tool
    if tool_name in ('Bash', 'PowerShell'):
        return _match_bash(content, invocation)
    canon = _FILE_CANON.get(tool_name, tool_name)
    if canon != tool_name:
        return False  # Write/NotebookEdit/MultiEdit/Glob path rules never match (validator warns)
    return _match_file(content, invocation)


def decide(rules_by_tier, tool_name, invocation):
    """Mirrors Zt(): deny > ask > allow > passthrough; first matching rule in tier wins.
    rules_by_tier: dict tier -> list of rules in merge order."""
    for tier in ('deny', 'ask', 'allow'):
        for rule in rules_by_tier.get(tier, []):
            if rule_matches(rule, tool_name, invocation):
                return tier, rule
    return 'passthrough', None


# ---------------------------------------------------------------- self-test

def _t(cond, label):
    print(('PASS' if cond else 'FAIL'), '-', label)
    return cond


def selftest():
    ok = True
    # parser
    ok &= _t(parse_rule('Bash')['kind'] == 'bare', 'bare rule')
    ok &= _t(parse_rule('Bash(npm run test)')['kind'] == 'call', 'call rule')
    ok &= _t(parse_rule('Bash(test))junk')['kind'] == 'malformed', 'trailing chars after ) -> malformed')
    ok &= _t(parse_rule('Bash(npm (test)')['kind'] == 'call', 'inner parens are literal, still a call')
    ok &= _t(parse_rule('Edit(src/**)')['rawContent'] == 'src/**', 'content kept verbatim')
    ok &= _t(normalize_rule('Bash(*)')['ruleContent'] is None, 'Bash(*) normalizes to bare')
    # validator
    ok &= _t(validate_rule('')[0] is False, 'empty invalid')
    ok &= _t(validate_rule('Bash()')[0] is False, 'empty parens invalid')
    ok &= _t(validate_rule('bash')[0] is False, 'lowercase tool invalid')
    ok &= _t(validate_rule('Bash(*)', 'allow')[0] is True, 'Bash(*) normalizes, valid')
    ok &= _t(validate_rule('mcp__puppeteer__*', 'allow')[0] is True, 'mcp allow wildcard ok')
    ok &= _t(validate_rule('mcp__srv__too*l', 'deny')[0] is True, 'deny wildcard ok')
    ok &= _t(validate_rule('Edit(foo:*x)', 'allow')[0] is False, ':* on file tool invalid')
    w = validate_rule('Write(src/**)', 'allow')[2]
    ok &= _t(any('only Edit(path)' in x for x in w), 'Write(path) warns -> use Edit')
    w = validate_rule('Glob(**)', 'allow')[2]
    ok &= _t(any('only Read(path)' in x for x in w), 'Glob(path) warns -> use Read')
    # matching: prefix semantics incl. bare-prefix match
    ok &= _t(rule_matches('Bash(git *)', 'Bash', 'git status'), 'git * matches git status')
    ok &= _t(rule_matches('Bash(git *)', 'Bash', 'git'), 'git * matches bare git')
    ok &= _t(not rule_matches('Bash(git *)', 'Bash', 'github'), 'git * does not match github')
    ok &= _t(rule_matches('Bash(npm run test)', 'Bash', 'NPM RUN TEST'), 'exact, case-insensitive')
    ok &= _t(rule_matches('Bash(npm run *)', 'Bash', 'npm run build'), 'wildcard')
    ok &= _t(not rule_matches('Bash(npm run *)', 'Bash', 'npm install'), 'wildcard non-match')
    ok &= _t(rule_matches('Edit(src/**)', 'Edit', 'src/a/b.ts'), 'globstar path')
    ok &= _t(rule_matches('Edit(**/*.test.ts)', 'Edit', 'a/b.test.ts'), 'globstar filename')
    ok &= _t(not rule_matches('Write(src/**)', 'Write', 'src/a.ts'), 'Write(path) never matches')
    ok &= _t(rule_matches('Read', 'Read', '/etc/passwd'), 'bare tool matches all')
    # decision ordering
    tiers = {'deny': ['Bash(rm *)'], 'ask': ['Bash'], 'allow': ['Bash(git *)']}
    ok &= _t(decide(tiers, 'Bash', 'rm -rf /') == ('deny', 'Bash(rm *)'), 'deny beats ask/allow')
    ok &= _t(decide(tiers, 'Bash', 'ls')[0] == 'ask', 'ask beats allow')
    ok &= _t(decide(tiers, 'Bash', 'echo hi')[0] == 'ask', 'bare Bash ask rule')
    tiers2 = {'deny': ['Bash(rm *)'], 'allow': ['Bash(git *)']}
    ok &= _t(decide(tiers2, 'Bash', 'git status') == ('allow', 'Bash(git *)'), 'allow matches')
    ok &= _t(decide(tiers, 'Bash', 'echo hi')[0] == 'ask', 'bare Bash ask rule')
    ok &= _t(decide({}, 'Bash', 'echo hi')[0] == 'passthrough', 'no rules -> passthrough')
    print('ALL PASS' if ok else 'SOME FAILURES')
    return ok


if __name__ == '__main__':
    sys.exit(0 if selftest() else 1)
