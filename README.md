# Minus E
[Website](https://minusetheartbot.github.io) | [Instagram](https://www.instagram.com/minusetheartbot/) | [Twitter](https://twitter.com/minusetheartbot)

A robot that does fine arts.

![logo](./media/logo.jpg)

## Usage

### server.py

```
usage: server.py [-h] [-p PORT] [-o] [-d]

Minus E - Server

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  specify the port number
  -o, --oled            Toggle OLED display
  -d, --debug           Toggle debugging info
```

### client.py

```
usage: client.py [-h] [-m] [-b] [-d] [-o] [-c] [-r RESOLUTION] [-mar MARGIN]
                 [-id INDEX] [-dp {0,2,4,8,16,32,64,128,256}] [-i IMAGE]

Minus E - Client

optional arguments:
  -h, --help            show this help message and exit
  -m, --monitor         Toggle monitor
  -b, --botless         Toggle botless
  -d, --debug           Toggle debug
  -o, --out             Toggle output
  -c, --crop            Toggle crop
  -r RESOLUTION, --resolution RESOLUTION
                        Specify the resolution of the drawing
  -mar MARGIN, --margin MARGIN
                        Specify the margin of the drawing
  -id INDEX, --index INDEX
                        specify the initial index
  -dp {0,2,4,8,16,32,64,128,256}, --depth {0,2,4,8,16,32,64,128,256}
                        specify the color depth
  -i IMAGE, --image IMAGE
                        path to the reference image file

```

## License
Minus E is under the [Apache license](./LICENSE).
