import os, sys, json, datetime
import subprocess as sp
import exif
from .. import config
from ..db import DataTypes as dt, Column, ModelBase, new_session

class Photograph(ModelBase):
    __tablename__ = 'photographs'

    signature     = Column(dt.Text, primary_key=True)
    basename      = Column(dt.Text)              
    mimetype      = Column(dt.Text)
    basename      = Column(dt.Text)
    fullpath      = Column(dt.Text)
    format        = Column(dt.Text)
    filesize      = Column(dt.Text)
    width         = Column(dt.Integer)
    height        = Column(dt.Integer)
    depth         = Column(dt.Integer)
    datetime      = Column(dt.DateTime)
    focal_length  = Column(dt.Float)
    f_stop        = Column(dt.Float)
    gamma         = Column(dt.Float)
    exp_bias      = Column(dt.Float)
    exp_mode      = Column(dt.Text)
    exp_program   = Column(dt.Text)
    exp_time      = Column(dt.Float)
    shutter       = Column(dt.Text)
    white_balance = Column(dt.Text)
    flash_fired   = Column(dt.Text)
    flash_mode    = Column(dt.Text)
    iso           = Column(dt.Integer)
    metering_mode = Column(dt.Text)
    camera_make   = Column(dt.Text)
    camera_model  = Column(dt.Text)
    lens          = Column(dt.Text)
    metadata_json = Column(dt.Text)
    thumbnail_data = Column(dt.Blob)

    thumbnail     = None

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

        self.metadata_json = json.dumps(jdata)

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
        if format in {'JPEG','GIF','PNG','TIFF','BMP'}:
            self.mimetype = 'image/%s' % self.format.lower()
        elif format == 'JPG':
            self.mimetype = 'image/JPG'
        elif format == 'TIF':
            self.mimetype = 'image/tiff'
        elif format in {'CRAW','CR2','CR3'}:
            self.mimetype = 'image/x-canon-%s' % self.format.lower()
        else:
            self.mimetype = 'unknown'
            
        # image data
        self.width    = geom.get('width', 0) 
        self.height   = geom.get('height', 0)
        self.depth    = img.get('depth', 0)
        self.gamma    = img.get('gamma', 0.0)

        # exif data
        self.focal_length = _exifFractVal(props.get('exif:FocalLength','0.0'))
        self.f_stop       = _exifFractVal(props.get('exif:FNumber','0.0'))
        self.exp_time     = _exifFractVal(props.get('exif:ExposureTime', '0.0'))
        self.shutter      = props.get('exif:ExposureTime', '')
        self.exp_bias     = _exifFractVal(props.get('exif:ExposureBiasValue','0.0'))
        self.iso          = int(props.get('exif:PhotographicSensitivity','0'))
        self.camera_make  = props.get('exif:Make','')
        self.camera_model = props.get('exif:Model', '')

        if 'exif:Gamma' in props:
            self.gamma        = _exifFractVal( props['exif:Gamma'] )
        
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

    def fromFile(self, path):
        proc = sp.Popen( [ config.IMAGE_MAGICK_BIN, 'convert', path, 'json:'], stdout=sp.PIPE, stderr=sp.PIPE )
        out, err = proc.communicate()
        ret = proc.returncode

        if ret == 0:
            jdata = json.loads(out)
            self.loadJSON(jdata[0])
        else:
            raise RuntimeError('ImageMagick subprocess encountered an error (return %i):\n%s' 
                                % (ret, err.decode(errors='ignore'))
            )
                
    # ---------------------------------------

    def createThumbnail( self, size=128, quality=80):
        import io, PIL
        
        cmd = [ config.IMAGE_MAGICK_BIN, 
            'convert', self.fullpath, 
            '-thumbnail','%ix%i' % (size,size),
            '-quality','%i' % quality,
            'jpeg:-'
        ]

        proc = sp.Popen( cmd, stdout=sp.PIPE, stderr=sp.PIPE )
        out, err = proc.communicate()

        try:
            img = PIL.Image.open(io.BytesIO(out))
            self.thumbnail_data, self.thumbnail = out, img
            return img
        except Exception:
            raise RuntimeError('Unable to generate thumbnail: ' + err.decode() )

    # ---------------------------------------

    def loadThumbnail(self):
        # we don't have to do this if already generated
        if not self.thumbnail == None: return self.thumbnail

        import io, PIL
        img = PIL.Image.open(io.BytesIO(self.thumbnail_data))
        self.thumbnail = img
        return img

    # ---------------------------------------
    
    def saveToDB(self):
        sess = new_session()

        # check if this key already exists, delete if it does
        chk = sess.query(self.__class__).get(self.signature)
        if chk: sess.delete(chk)

        sess.add(self)
        sess.commit()
        sess.close()

    # ----------------------------------------

    def loadFromDB(self, signature ):
        sess = new_session()

        r = sess.query(self.__class__).get(signature)
        
        for k in self._sa_class_manager.mapper.columns.keys():
            setattr( self, k, getattr(r,k) )
        sess.close()

        return r
    
    # ----------------------------------------