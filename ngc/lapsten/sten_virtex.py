from util import CNC

cnc = CNC(em=0.0413)
cnc.rect_in_ul(x=-0.403, y=-0.864, w=0.805, h=0.789)
cnc.rect_in_ul(x=-0.403, y=-0.075, w=0.805, h=0.789)
cnc.circ_cent_out(x=0.0, y=0.0, r=1.063)
cnc.end()

