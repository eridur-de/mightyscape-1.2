from __future__ import annotations
from functools import singledispatchmethod
from typing import Final
import inkex
from desc_parser import clear_description

class SetMaterial(inkex.EffectExtension):
    """Writes the chosen optical property in the element description"""

    # only change the description for these objects
    filter_primitives: Final = (
        inkex.PathElement,
        inkex.Line,
        inkex.Polyline,
        inkex.Polygon,
        inkex.Rectangle,
        inkex.Ellipse,
        inkex.Circle,
    )

    def __init__(self):
        super().__init__()

    def add_arguments(self, pars):
        pars.add_argument("--optical_material", default="none", help="Name of the optical material to convert the selection to.")
        pars.add_argument("--optical_index", type=float, default=1.5168)

    def effect(self) -> None:
        filter_ = self.filter_primitives + (inkex.Group,)
        for obj in self.svg.selection.filter(filter_):
            self.update_description(obj)

    @singledispatchmethod
    def update_description(self, arg):
        pass

    @update_description.register
    def _(self, group: inkex.Group):
        for obj in group:
            self.update_description(obj)

    for type in filter_primitives:

        @update_description.register(type)
        def _(self, obj):
            """
            In the description of the element, replaces the optical properties
            with the new one.
            """

            desc = obj.desc
            if desc is None:
                desc = ""
            new_desc = clear_description(desc)
            if desc != "" and desc[-1] != "\n":
                desc += "\n"

            material_name = self.options.optical_material
            if material_name is not None:
                new_desc += f"optics:{material_name}"
                if material_name == "glass":
                    new_desc += f":{self.options.optical_index:.4f}"
            obj.desc = new_desc


if __name__ == "__main__":
    SetMaterial().run()