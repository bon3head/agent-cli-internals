#!/usr/bin/env python3
"""C1 PoC: settings.json validator against the schema recovered from claude 2.1.287.

Key list : deep-dive/ia-keys.txt (192 keys from Ia()) + 7 unit keys from wn
           (skipAutoPermissionPrompt, useAutoModeDuringPlan, autoMode,
            disableDeepLinkRegistration, voiceEnabled, defaultView, axScreenReader)
Types    : deep-dive/ia-schema-parsed.txt (zod heads classified: o=str, M=bool,
           k/ib=number, A=list, u=dict, B([...])=enum, x("lit")=literal)
Rules    : c1-permission-matcher.validate_rule for permissions.allow/deny/ask
Hooks    : event names vs the 33-event enum (kg); hook type literals
           {command, prompt, mcp_tool, http, agent}; required fields per type.

IMPORTANT: the runtime schema is .passthrough() — unknown keys are KEPT, not
rejected. So unknown keys are warnings here, never errors. (CONFIRMED: An.whole()
= u(shapeOf(keys)).passthrough().)

Usage: python3 c1-settings-validator.py <settings.json> [more...]
Exit 0 = no errors (warnings ok), 1 = errors found.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DD = os.path.dirname(HERE)
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location('c1_permission_matcher',
                                     os.path.join(HERE, 'c1-permission-matcher.py'))
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
validate_rule = _mod.validate_rule

HOOK_EVENTS = """PreToolUse PostToolUse PostToolUseFailure PostToolBatch Notification
UserPromptSubmit UserPromptExpansion SessionStart SessionEnd Stop StopFailure SubagentStart
SubagentStop PreCompact PostCompact PreModelSwitch PostModelSwitch PermissionRequest
PermissionDenied Setup TeammateIdle TaskCreated TaskCompleted Elicitation ElicitationResult
ConfigChange WorktreeCreate WorktreeRemove InstructionsLoaded CwdChanged FileChanged
DirectoryAdded MessageDisplay""".split()

HOOK_TYPES = {
    'command': ['command'],
    'prompt': ['prompt'],
    'mcp_tool': ['server', 'tool'],
    'http': ['url'],
    'agent': ['prompt'],
}

PERMISSION_MODES = ['acceptEdits', 'auto', 'bypassPermissions', 'default', 'dontAsk', 'plan', 'manual']

_UNIT_KEYS = ['skipAutoPermissionPrompt', 'useAutoModeDuringPlan', 'autoMode',
              'disableDeepLinkRegistration', 'voiceEnabled', 'defaultView', 'axScreenReader']


def _load_keys():
    keys = {}
    with open(os.path.join(DD, 'ia-keys.txt')) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('<???>'):
                keys[line] = None
    for k in _UNIT_KEYS:
        keys[k] = None
    return keys


def _load_types():
    """Parse ia-schema-parsed.txt into {key: (kind, enum_values)}."""
    types = {}
    cur = None
    with open(os.path.join(DD, 'ia-schema-parsed.txt')) as f:
        for line in f:
            m = re.match(r'### (\S+)', line)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r'\s*type: (.*)', line)
            if m and cur:
                head = m.group(1)
                kind = 'unknown'
                enum = None
                if head.startswith('o()'):
                    kind = 'str'
                elif head.startswith('M()'):
                    kind = 'bool'
                elif head.startswith('k()') or head.startswith('ib()'):
                    kind = 'number'
                elif head.startswith('A('):
                    kind = 'list'
                elif head.startswith('u({'):
                    kind = 'dict'
                elif head.startswith('B(['):
                    kind = 'enum'
                    enum = re.findall(r'"([^"]+)"', head.split('])')[0])
                elif head.startswith('x('):
                    kind = 'literal'
                    mm = re.search(r'"([^"]+)"', head)
                    enum = [mm.group(1)] if mm else []
                elif head.startswith('$e(') or head.startswith('Ae('):
                    kind = 'any'
                types[cur] = (kind, enum)
    return types


KEYS = _load_keys()
TYPES = _load_types()

_PYTYPE = {'str': str, 'bool': bool, 'number': (int, float), 'list': list, 'dict': dict}


def _check_value(key, value, path, errors, warnings):
    kind, enum = TYPES.get(key, ('unknown', None))
    if kind in _PYTYPE:
        want = _PYTYPE[kind]
        # bool is subclass of int; exclude bool where number expected and vice versa
        if kind == 'number' and isinstance(value, bool):
            errors.append(f'{path}: expected number, got bool')
        elif kind == 'bool' and not isinstance(value, bool):
            errors.append(f'{path}: expected bool, got {type(value).__name__}')
        elif kind != 'number' and kind != 'bool' and not isinstance(value, want):
            errors.append(f'{path}: expected {kind}, got {type(value).__name__}')
    elif kind == 'enum' and enum is not None:
        if value not in enum:
            errors.append(f'{path}: expected one of {enum}, got {value!r}')
    elif kind == 'literal' and enum:
        if value not in enum:
            errors.append(f'{path}: expected {enum[0]!r}, got {value!r}')


def _check_permissions(perms, errors, warnings):
    if not isinstance(perms, dict):
        errors.append('permissions: expected object')
        return
    for tier in ('allow', 'deny', 'ask'):
        rules = perms.get(tier, [])
        if not isinstance(rules, list):
            errors.append(f'permissions.{tier}: expected array of rule strings')
            continue
        for i, r in enumerate(rules):
            if not isinstance(r, str):
                errors.append(f'permissions.{tier}[{i}]: expected string')
                continue
            ok, problems, warns = validate_rule(r, tier if tier == 'allow' else 'deny')
            for p in problems:
                errors.append(f'permissions.{tier}[{i}] {r!r}: {p}')
            for w in warns:
                warnings.append(f'permissions.{tier}[{i}] {r!r}: {w}')
    dm = perms.get('defaultMode')
    if dm is not None and dm not in PERMISSION_MODES:
        errors.append(f'permissions.defaultMode: expected one of {PERMISSION_MODES}, got {dm!r}')
    dbp = perms.get('disableBypassPermissionsMode')
    if dbp is not None and dbp != 'disable':
        errors.append('permissions.disableBypassPermissionsMode: only value is "disable"')
    for k in ('blockReadsOutsideWorkingDirectories',):
        if k in perms and not isinstance(perms[k], bool):
            errors.append(f'permissions.{k}: expected bool')


def _check_hooks(hooks, errors, warnings):
    if not isinstance(hooks, dict):
        errors.append('hooks: expected object keyed by event name')
        return
    for event, entries in hooks.items():
        if event not in HOOK_EVENTS:
            errors.append(f'hooks: unknown event {event!r} (expected one of the 33 hook events)')
            continue
        if not isinstance(entries, list):
            errors.append(f'hooks.{event}: expected array of {{matcher, hooks}} entries')
            continue
        for i, entry in enumerate(entries):
            p = f'hooks.{event}[{i}]'
            if not isinstance(entry, dict):
                errors.append(f'{p}: expected object')
                continue
            hs = entry.get('hooks')
            if not isinstance(hs, list) or not hs:
                errors.append(f'{p}.hooks: expected non-empty array of hook entries')
                continue
            for j, h in enumerate(hs):
                hp = f'{p}.hooks[{j}]'
                if not isinstance(h, dict):
                    errors.append(f'{hp}: expected object')
                    continue
                t = h.get('type')
                if t not in HOOK_TYPES:
                    errors.append(f'{hp}.type: expected one of {sorted(HOOK_TYPES)}, got {t!r}')
                    continue
                for req in HOOK_TYPES[t]:
                    if req not in h:
                        errors.append(f'{hp}: hook type {t!r} requires {req!r}')


def validate_file(path):
    errors, warnings = [], []
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f'{path}: Invalid JSON: {e}'], []
    if not isinstance(data, dict):
        return [f'{path}: top level must be a JSON object'], []
    for key, value in data.items():
        if key not in KEYS:
            warnings.append(f'{key}: unknown key (schema is passthrough: kept, not rejected)')
            continue
        _check_value(key, value, key, errors, warnings)
        if key == 'permissions':
            _check_permissions(value, errors, warnings)
        elif key == 'hooks':
            _check_hooks(value, errors, warnings)
    return errors, warnings


def main(paths):
    failed = False
    for path in paths:
        errors, warnings = validate_file(path)
        print(f'== {path}: {len(errors)} error(s), {len(warnings)} warning(s)')
        for e in errors:
            print('  ERROR:', e)
        for w in warnings:
            print('  warn: ', w)
        if errors:
            failed = True
    return 1 if failed else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
