import os, sys, json, datetime
import exif

class Photograph():

    def __init__(self):
        self.signature     = ''             
        self.basename      = ''              
        self.mimetype      = ''
        self.basename      = ''
        self.fullpath      = ''
        self.format        = ''
        self.filesize      = ''
        self.width         = 0
        self.height        = 0
        self.depth         = 0
        self.datetime      = None
        self.focal_length  = 0.0
        self.f_stop        = 0.0
        self.gamma         = 0.0
        self.exp_bias      = 0.0
        self.exp_mode      = ''
        self.exp_program   = ''
        self.exp_time      = 0.0
        self.shutter       = ''
        self.white_balance = ''
        self.flash_fired   = ''
        self.flash_mode    = ''
        self.iso           = 0
        self.metering_mode = ''
        self.camera_make   = ''
        self.camera_model  = ''
        self.lens          = ''
        self.metadata_json = ''

    # ----------------------------------------

    def __str__(self):
        return "<Photograph> id:%s %s %ix%ix%i %s" % \
                (self.signature[0:12], self.format, self.width, self.height, self.depth, self.datetime )
    
    # ----------------------------------------

    def __repr__(self):
        r = [ "<Photograph> id:%s %s %ix%ix%i %s" %
                        (self.signature[0:12], self.format, self.width, 
                         self.height, self.depth, self.datetime )
        ]
        
        if len(self.camera_model) > 0:
            r.append( "%s %s %s %s f%0.1f ISO%i Exp:%0.2f %s" % (self.camera_make, 
                                  self.camera_model.replace(self.camera_make,''),
                                  self.lens, self.shutter, self.f_stop, self.iso, self.exp_bias,
                                  '[FLASH]' if self.flash_fired == 'True' else '',
               )
            )
        
        if len(self.fullpath) > 0:
            r.append("  file:///%s [%s]" % ( self.fullpath.replace('\\','/'),
                                           self.filesize if len(self.filesize) > 0 else '???'
                                           )
            )
        
        
        return '\n'.join(r)

    # ----------------------------------------

    def loadJSON(self, jdata):
        """
        Populate from Image Magick JSON dump.
        """

        if isinstance(jdata, ( str, type(b'a'),type(u'a') ) ):
            jdata = json.loads(jdata)

        def _exifFractVal( v ):
            parts = [ x.strip() for x in v.split('/') ]
            parts = [ x for x in parts if len(x) > 0 ]
            
            if len(parts) < 1: 
                return None
            elif len(parts) < 2: 
                return float(parts[0])
            else:
                return float(parts[0]) / float(parts[1])

        # ------------------------------------

        def _getDateTime( img ):
            props = img.get('properties',{})

            tags = ('exif:DateTimeOriginal', 'exif:DateTimeDigitized',
                    'exif:DateTime', 'dng:create.date',
                    'date:modify',  'date:create',
            )

            fmts = ('%Y:%m:%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S' )

            dates = []

            for t in tags:
                if not t in props: continue

                v = props[t].split('+')[0]

                parsed = None
                
                for f in fmts:
                    try:
                        parsed = datetime.datetime.strptime(v, f)
                        break
                    except Exception as ex:
                        pass
                
                if parsed: dates.append(parsed)
            # --------------------------

            dates.sort()
            if len(dates) < 1: return None
            return dates[0]

        # ------------------------------------

        self.metadata_json = jdata

        img   = jdata.get('image', {})
        geom  = img.get('geometry', {})
        props = img.get('properties', {})

        exif_keys = { x for x in props.keys() if x.lower().find('exif:') == 0 }
        prop_keys = { x for x in props.keys() if x not in exif_keys }
            
        # file data
        self.signature = props.get('signature','')
        self.fullpath  = img.get('name', '')
        self.filesize  = img.get('filesize','')
        self.basename  = os.path.basename(self.fullpath)
        self.format    = img.get('format', '').upper().strip()

        # set the mime type
        if self.format in {'JPEG','GIF','PNG','TIFF','BMP'}:
            self.mimetype = 'image/%s' % self.format.lower()
        elif self.format == 'JPG':
            self.mimetype = 'image/JPG'
        elif self.format == 'TIF':
            self.mimetype = 'image/tiff'
        elif self.format in {'CRAW','CR2','CR3'}:
            self.mimetype = 'image/x-canon-%s' % self.format.lower()
        else:
            self.mimetype = 'unknown'
            
        # image data
        self.width    = geom.get('width', 0) 
        self.height   = geom.get('height', 0)
        self.depth    = img.get('depth', 0)

        # exif data
        self.focal_length = _exifFractVal(props.get('exif:FocalLength',''))
        self.f_stop       = _exifFractVal(props.get('exif:FNumber',''))
        self.exp_time     = _exifFractVal(props.get('exif:ExposureTime', ''))
        self.shutter      = props.get('exif:ExposureTime', '')
        self.exp_bias     = _exifFractVal(props.get('exif:ExposureBiasValue',''))
        self.iso          = int(props.get('exif:PhotographicSensitivity','0'))
        self.camera_make  = props.get('exif:Make','')
        self.camera_model = props.get('exif:Model', '')

        # exif data - enumerations

        #Exposure Mode
        if 'exif:ExposureMode' in props:
            self.exp_mode = exif.ExposureMode( int(props['exif:ExposureMode']) ).name

        if 'exif:ExposureProgram' in props:
            self.exp_program = exif.ExposureProgram( int(props['exif:ExposureProgram']) ).name

        if 'exif:WhiteBalance' in props:
            self.white_balance = exif.WhiteBalance( int(props['exif:WhiteBalance']) ).name

        if 'exif:MeteringMode' in props:
            self.metering_mode = exif.MeteringMode( int(props['exif:MeteringMode']) ).name

        if 'exif:Flash' in props:
            _flash = exif.Flash( int(props['exif:Flash']) )
            self.flash_fired = str( _flash.flash_fired )
            self.flash_mode  = _flash.flash_mode.name

        # dng (CR2) data
        if len(exif_keys) < 1:
            self.focal_length  = float(props.get('dng:ocal.length','0.0'))
            self.f_stop        = float(props.get('dng:f.number','0.0'))
            self.lens          = props.get('dng:lens', '')
            self.camera_make   = props.get('dng:make', '')
            self.camera_model  = props.get('dng:camera.model.name','')
            self.camera_serial = props.get('dng:serial.number') 
            self.iso           = int( float(props.get('dng:iso.setting','0')) )
            self.exp_time      = _exifFractVal(props.get('dng:exposure.time',''))
            self.shutter       = props.get('dng:exposure.time','0')
            
        #decode the datetime
        self.datetime = _getDateTime(img)

    # ----------------------------------------