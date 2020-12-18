# OrienteeringAI
@Author: Brian Finnerty

Implementation of A* search for region colored maps of Mendon Ponds Park

This project was based around color coded maps of Mendon Ponds Park during various times of year. This project was developed to test
my knowledge of the A* search algorithm, my usage of heuristics and the implementation of my cost function.

The inputs for this are a color coded terrian image, an elevation file that details the elevation of each pixel, a list of points in which the A* search must path through,
the season of the image, and finally a name for the resulting output.

The output of this program is an image file which takes the input file and traces the optimal path  to take for the given points.
