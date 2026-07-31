"""Citation text shared by the CLI and GUI (`rheology-fit cite`)."""

from rheology_fit import __version__

CITATION_APA = (
    "Khachatryan, K. (2026). rheology-fit: fitting non-Newtonian flow curve "
    "models to shear stress/rate data for food rheology (Version "
    f"{__version__}) [Computer software]. "
    "University of Agriculture in Krakow. https://doi.org/10.5281/zenodo.21713809"
)

CITATION_BIBTEX = f"""@software{{khachatryan_rheology_fit_2026,
  author  = {{Khachatryan, Karen}},
  title   = {{rheology-fit: fitting non-Newtonian flow curve models to shear stress/rate data for food rheology}},
  year    = {{2026}},
  version = {{{__version__}}},
  doi     = {{10.5281/zenodo.21713809}},
  url     = {{https://github.com/karenkhachatryan-lab/rheology-fit}}
}}"""
