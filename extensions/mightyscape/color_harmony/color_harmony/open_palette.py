def load_palette(filename, mixer=None, options=None):
    if mixer is None:
        mixer = mixers.MixerRGB
    loader = detect_storage(filename)
    if loader is None:
        return None
    palette = loader().load(mixer, filename, options)
    return palette

def save_palette(palette, path, formatname=None):
    if formatname is not None:
        loader = get_storage_by_name(formatname)
    else:
        loader = detect_storage(path, save=True)
    if loader is None:
        raise RuntimeError("Unknown file type!")
    loader(palette).save(path)
