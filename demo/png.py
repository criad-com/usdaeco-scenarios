"""Small PNG content reader for usdrecord images; no imaging wheel is required."""
from pathlib import Path
import struct
import zlib
import numpy as np


def pixels(path, *, alpha=False):
    raw=Path(path).read_bytes()
    if raw[:8]!=b'\x89PNG\r\n\x1a\n':
        raise ValueError('Not a PNG image')
    offset=8;compressed=bytearray();header=None
    while offset<len(raw):
        length=struct.unpack('>I',raw[offset:offset+4])[0]
        kind=raw[offset+4:offset+8];data=raw[offset+8:offset+8+length]
        if kind==b'IHDR':header=struct.unpack('>IIBBBBB',data)
        if kind==b'IDAT':compressed.extend(data)
        offset+=length+12
    width,height,depth,colour,compression,filtering,interlace=header
    if depth!=8 or colour not in (2,6) or interlace:
        raise ValueError('Expected non-interlaced 8-bit RGB/RGBA from usdrecord')
    channels=3 if colour==2 else 4;stride=width*channels
    scan=zlib.decompress(compressed);decoded=np.zeros((height,stride),dtype=np.uint8)
    for y in range(height):
        mode=scan[y*(stride+1)];row=np.frombuffer(scan[y*(stride+1)+1:(y+1)*(stride+1)],dtype=np.uint8).copy()
        prior=decoded[y-1] if y else np.zeros(stride,dtype=np.uint8)
        if mode==1:
            for channel in range(channels):row[channel::channels]=np.cumsum(row[channel::channels],dtype=np.uint64)%256
        elif mode==2:row=(row.astype(np.uint16)+prior)%256
        elif mode in (3,4):
            for x in range(stride):
                a=int(row[x-channels]) if x>=channels else 0;b=int(prior[x]);c=int(prior[x-channels]) if x>=channels else 0
                if mode==3:predictor=(a+b)//2
                else:
                    p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
                    predictor=a if pa<=pb and pa<=pc else b if pb<=pc else c
                row[x]=(int(row[x])+predictor)%256
        elif mode!=0:raise ValueError('Unsupported PNG filter')
        decoded[y]=row
    return decoded.reshape(height,width,channels)[:,:,:4 if alpha else 3].astype(float)/255.
