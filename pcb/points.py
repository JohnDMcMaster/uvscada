import math

def simple():
    '''
    3.14 * 0.5 = 1.57
    1.57 / 40 = 0.03925
    take half => 0.019625
    20 mil diameter pads

    
    
    rond
    6 mil fab rule?
    20 mil hole, 10 mil ring each side
    should be fine
    
    eh pretty tight
    lets shrink slightly
    '''

    D = 0.5
    R = D / 2
    PINS = 40

    for i in xrange(PINS):
        pin = i + 1
        angle = (i + 0.5) * 2 * math.pi / PINS
        if angle > 2 * math.pi:
            angle -= 2 * math.pi
        angle = -angle
        x = R * math.sin(angle)
        y = R * math.cos(angle)
        print '% 3d: % 4d x % 4d y % 5d r' % (pin, 1000 * x, 1000 * y, -360 * angle / 3.14 / 2 )



'''
autogen
pcad.lia simple

.dxf may also work

figured out how to import .lia
do that



OSH rules
https://oshpark.com/guidelines
6 mil minimum trace width
6 mil minimum spacing
at least 15 mil clearances from traces to the edge of the board
13 mil minimum drill size
7 mil minimum annular ring

pcbway rules
http://www.pcbway.com/capabilities.html
drill size
    Min drill size is 0.2mm, 
        7.9 mil
    max drill is 6.3mm. 
    Any holes greater than 6.3mm or smaller than 0.3mm will be subject to extra charges. 
        6.3: 248 mil
        0.3: 11.8 mil

Min Width of Annular Ring 
    0.15mm(6mil) 

Minimum Diameter of Plated Half Holes 
0.6mm
eeeeh
that messes up what I'm trying to do
23.6 mil
actually maybe its okay


so in summary
current
    hole: 13
    annular ring: 7
    net size: 27

move to
    hole: 12
    annular ring: 6
    net size: 24

eliminated most but not all
need 1 more mil
hole 12





0.5 * 3.14159 = 1.570795
1.570795 / 28 = 0.056099821
56 mil
6 mil spacing min
7 mil minimum annular ring

0.1" fencepost ref
    40
    68
9 mil ring


say 9 mil spacing
9 mil ring
56 - 9 - 2 * 9 = 29 hole
wait no hole

just do it evenly
56/2 = 28
'''

def header():
    return '''\
ACCEL_ASCII "POINTS.LIA"

(asciiHeader
  (asciiVersion 3 0)
  (timeStamp 2017 1 7 0 54 1)
  (program "points.py" "1.0.0")
  (copyright "points.py")
  (headerString "")
  (fileUnits Mil)
  (guidString "{00000000-0000-0000-0000-000000000000}")
)

(library "Library_1"
  (padStyleDef "(Default)"
    (holeDiam 30mil)
    (startRange 1)
    (endRange 2)
    (padShape (layerNumRef 1) (padShapeType Oval) (shapeWidth 60mil) (shapeHeight 60mil) )
    (padShape (layerNumRef 2) (padShapeType Oval) (shapeWidth 60mil) (shapeHeight 60mil) )
    (padShape (layerType Signal) (padShapeType Oval) (shapeWidth 60mil) (shapeHeight 60mil) )
    (padShape (layerType Plane) (padShapeType NoConnect) (shapeWidth 0.0) (shapeHeight 0.0) )
    (padShape (layerType NonSignal) (padShapeType Oval) (shapeWidth 0mil) (shapeHeight 0mil) )
  )
  (padStyleDef "EF20X60TOP1"
    (holeDiam 0mil)
    (startRange 1)
    (endRange 2)
    (padShape (layerNumRef 1) (padShapeType Oval) (shapeWidth 20mil) (shapeHeight 60mil) )
    (padShape (layerNumRef 2) (padShapeType Ellipse) (shapeWidth 0.0) (shapeHeight 0.0) )
    (padShape (layerType Signal) (padShapeType Oval) (shapeWidth 0.0) (shapeHeight 0.0) )
    (padShape (layerType Plane) (padShapeType NoConnect) (shapeWidth 0.0) (shapeHeight 0.0) )
    (padShape (layerType NonSignal) (padShapeType Oval) (shapeWidth 0mil) (shapeHeight 0mil) )
  )
  (padStyleDef "P:EX30Y30D201"
    (holeDiam 12mil)
    (startRange 1)
    (endRange 2)
    (padShape (layerNumRef 1) (padShapeType Oval) (shapeWidth 24mil) (shapeHeight 24mil) )
    (padShape (layerNumRef 2) (padShapeType Oval) (shapeWidth 24mil) (shapeHeight 24mil) )
    (padShape (layerType Signal) (padShapeType Oval) (shapeWidth 24mil) (shapeHeight 24mil) )
    (padShape (layerType Plane) (padShapeType NoConnect) (shapeWidth 0.0) (shapeHeight 0.0) )
    (padShape (layerType NonSignal) (padShapeType Oval) (shapeWidth 0mil) (shapeHeight 0mil) )
  )
  (padStyleDef "RECT28"
    (holeDiam 0mil)
    (startRange 1)
    (endRange 2)
    (padShape (layerNumRef 1) (padShapeType Rect) (shapeWidth 28mil) (shapeHeight 28mil) )
    (padShape (layerNumRef 2) (padShapeType Ellipse) (shapeWidth 0.0) (shapeHeight 0.0) )
    (padShape (layerType Signal) (padShapeType Rect) (shapeWidth 28mil) (shapeHeight 28mil) )
    (padShape (layerType Plane) (padShapeType NoConnect) (shapeWidth 0.0) (shapeHeight 0.0) )
    (padShape (layerType NonSignal) (padShapeType Oval) (shapeWidth 0mil) (shapeHeight 0mil) )
  )
  (viaStyleDef "(Default)"
    (holeDiam 28mil)
    (startRange 1)
    (endRange 2)
    (viaShape (layerNumRef 1) (viaShapeType Ellipse) (shapeWidth 50mil) (shapeHeight 50mil) )
    (viaShape (layerNumRef 2) (viaShapeType Ellipse) (shapeWidth 50mil) (shapeHeight 50mil) )
    (viaShape (layerType Signal) (viaShapeType Ellipse) (shapeWidth 50mil) (shapeHeight 50mil) )
    (viaShape (layerType Plane) (viaShapeType NoConnect) (shapeWidth 0.0) (shapeHeight 0.0) )
    (viaShape (layerType NonSignal) (viaShapeType Ellipse) (shapeWidth 0mil) (shapeHeight 0mil) )
  )
  (textStyleDef "(Default)"
    (font
      (fontType Stroke)
      (fontFamily Modern)
      (fontFace "Quality")
      (fontHeight 80mil) 
      (strokeWidth 10mil) 
    )
    (textStyleAllowTType False)
    (textStyleDisplayTType False)
  )
  (textStyleDef "(DefaultTTF)"    
    (font                         
      (fontType Stroke)           
      (fontFamily SanSerif)       
      (fontFace "QUALITY")        
      (fontHeight 100.0)          
      (strokeWidth 10.0)          
    )                             
    (font                         
      (fontType TrueType)         
      (fontFamily Modern)         
      (fontFace "Arial")          
      (fontHeight 125.0)          
      (strokeWidth 0.19843 mm)    
      (fontWeight 400)            
      (fontCharSet 0)             
      (fontOutPrecision 7)        
      (fontClipPrecision 32)      
      (fontQuality 1)             
      (fontPitchAndFamily 6)      
    )                             
    (textStyleAllowTType True)    
    (textStyleDisplayTType True)  
  )                               
  (patternDefExtended "ROUND40-0.5_1"
  (originalName "ROUND40-0.5")
    (patternGraphicsNameRef "Primary")

    (patternGraphicsDef
      (patternGraphicsNameDef "Primary")
      (multiLayer
  '''

def footer(pins):
    s = '''\
      )
      (layerContents (layerNumRef 10)
        (arc (pt 0mil 0mil) (radius 250mil) (startAngle 0.0) (sweepAngle 360.0) (width 10mil) )
      )
      (layerContents (layerNumRef 6)
        (attr "RefDes" "" (pt -266.767mil 294.091mil) (isVisible True) (textStyleRef "(Default)") )
        (attr "Type" "" (pt -266.767mil -389mil) (isVisible True) (textStyleRef "(Default)") )
      )
    )
  )
  (compDef "ROUND40-0.5_1"
    (originalName "ROUND40-0.5")
    (compHeader
      (sourceLibrary "")
      (numPins 40)
      (numParts 1)
      (alts (ieeeAlt False) (deMorganAlt False))
      (refDesPrefix "")
    )
'''
    for i in xrange(pins):
        '''
        (compPin "1" (partNum 1) (symPinNum 1) (gateEq 0) (pinEq 0) )
        (compPin "2" (partNum 1) (symPinNum 1) (gateEq 0) (pinEq 0) )
        (compPin "3" (partNum 1) (symPinNum 1) (gateEq 0) (pinEq 0) )
        ...
        (compPin "40" (partNum 1) (symPinNum 1) (gateEq 0) (pinEq 0) )
        '''
        pin = i + 1
        s += '    (compPin "%d" (partNum 1) (symPinNum 1) (gateEq 0) (pinEq 0) )\n' % (pin,)
        
    s += '''\
    (attachedPattern (patternNum 1) (patternName "ROUND40-0.5")
      (numPads 40)
      (padPinMap
    '''
    
    for i in xrange(pins):
        '''
        (padNum 1) (compPinRef "1")
        (padNum 2) (compPinRef "2")
        (padNum 3) (compPinRef "3")
        ...
        (padNum 40) (compPinRef "40")
        '''
        pin = i + 1
        s += '        (padNum %d) (compPinRef "%d")\n' % (pin, pin)
    s += '''\
      )
    )
  )
)
'''
    return s

def auto(PINS=40, D=0.5, padStyleRef="EF20X60TOP1"):
    R = D / 2
    s = header()

    for i in xrange(PINS):
        pin = i + 1
        angler = (i + 0.5) * 2 * math.pi / PINS
        angler = -angler
        angled = angler * 180 / math.pi
        x = R * math.sin(angler)
        y = R * math.cos(angler)
        '''
        (pad (padNum 1) (padStyleRef "EF20X60TOP1") (pt -19mil 249mil) (rotation 4.0)(defaultPinDes "1"))
        (pad (padNum 2) (padStyleRef "EF20X60TOP1") (pt -58mil 243mil) (rotation 13.0)(defaultPinDes "2"))
        (pad (padNum 3) (padStyleRef "EF20X60TOP1") (pt -95mil 230mil) (rotation 22.0)(defaultPinDes "3"))
        '''
        # Rotation CW
        # Need to counter above rotation
        l = '        (pad (padNum %d) (padStyleRef "%s") (pt %dmil %dmil) (rotation %0.1f)(defaultPinDes "%d"))\n' % (pin, padStyleRef, 1000 * x, 1000 * y, -angled, pin)
        s += l

    s += footer(PINS)
    print s

# Original design
# Elongated oval pad sliced in the middle
#auto(PINS=40, D=0.5, padStyleRef="EF20X60TOP1")
# castillation
#auto(PINS=40, D=0.5, padStyleRef="P:EX30Y30D201")

# diameter
# pad size/2
# solder mask expansion
# edge clearance
#auto(PINS=28, D=0.5+0.056/2+2*0.004+2*0.006, padStyleRef="RECT28")
auto(PINS=28, D=0.45+0.056/2+2*0.004+2*0.006, padStyleRef="RECT28")

