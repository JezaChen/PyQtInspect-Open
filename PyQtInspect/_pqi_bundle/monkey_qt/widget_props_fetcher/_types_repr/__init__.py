from ._base import get_representation

# Import all type representation modules to register them but don't pollute the namespace
from . import _ordinary_types_reprs as _
from . import _enum_reprs as _
from . import _flag_reprs as _
