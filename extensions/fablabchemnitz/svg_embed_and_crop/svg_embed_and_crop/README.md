[Inkscape](http://inkscape.org/) is a powerful open-source
vector graphics editor which supports the inclusion of
raster images either through file references (links)
or through direct embedding of the image data in the 
Inkscape SVG file. Referencing images as links keeps SVG files
small and ensures that changes to image placement and 
transformations specified in the SVG file remain separate 
from the underlying image data. However, embedding images 
may be required as a final step in some production work-flows. 

This java-based extension for Inkscape facilitates 
image embedding by: 

-    Automatically identifying all linked images.
-    Cropping image data that lies outside the images'
     clipping frame.
-    Optionally applying jpeg compression.
-    Optionally resampling images above a maximum resolution
-    Writing the cropped and possibly compressed image
     data directly in the SVG file.

By cropping image data that lies outside the clipping frame,
applying jpeg compression, or resampling images above a maximum resolution,
the resulting file size can be reduced significantly.
Alternatively, if preserving image quality is a priority 
jpeg compression and resampling can be explicitly avoided.

The plugin uses [ImageJ](http://rsbweb.nih.gov/ij/)
to load and manipulate the image data and
the Apache Commons Codec library to encode
the data for embedding.

**[Installation instructions and documentation](http://b.nanes.org/svg-embed-and-crop/)**
