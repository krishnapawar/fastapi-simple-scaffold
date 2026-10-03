import re
import sys

def setup_terminal_encoding():
    """Ensure Windows terminal handles UTF-8 gracefully without charmap crashes."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

setup_terminal_encoding()


def to_snake_case(name: str) -> str:
    """Convert PascalCase, camelCase or kebab-case to snake_case."""
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
    s = re.sub(r'[-\s]+', '_', s)
    return s.lower().strip('_')

def to_pascal_case(name: str) -> str:
    """Convert snake_case, kebab-case or space-separated to PascalCase."""
    words = re.split(r'[-_\s]+', name)
    return ''.join(w.capitalize() for w in words if w)

def to_camel_case(name: str) -> str:
    """Convert to camelCase."""
    pascal = to_pascal_case(name)
    if not pascal:
        return ''
    return pascal[0].lower() + pascal[1:]

def to_kebab_case(name: str) -> str:
    """Convert to kebab-case."""
    return to_snake_case(name).replace('_', '-')

def pluralize(word: str) -> str:
    """Simple English pluralization for resource and table names."""
    w = word.strip()
    if not w:
        return ''
    lower = w.lower()
    if lower.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return w + 'es'
    elif lower.endswith('y') and len(w) > 1 and lower[-2] not in 'aeiou':
        return w[:-1] + 'ies'
    elif lower.endswith('fe'):
        return w[:-2] + 'ves'
    elif lower.endswith('f') and not lower.endswith('ff'):
        return w[:-1] + 'ves'
    elif lower.endswith('s'):
        return w
    return w + 's'

def singularize(word: str) -> str:
    """Simple English singularization."""
    w = word.strip()
    if not w:
        return ''
    lower = w.lower()
    if lower.endswith('ies') and len(w) > 3:
        return w[:-3] + 'y'
    elif lower.endswith('ves') and len(w) > 3:
        return w[:-3] + 'f'
    elif lower.endswith('es') and (lower.endswith('shes') or lower.endswith('ches') or lower.endswith('xes') or lower.endswith('sses') or lower.endswith('zes')):
        return w[:-2]
    elif lower.endswith('s') and not lower.endswith('ss'):
        return w[:-1]
    return w
