from PIL import Image, ImageDraw, ImageSequence
import io, sys, os

#use like : python gif2mock.py [my.gif/my.mp4] out.gif 48

#positions to paste screen and phone
SCREEN_POS = (257,295)
PHONE_POS = (248,270)


image_name = sys.argv[1]
status_cut = 48
if len(sys.argv) > 3:
	status_cut = sys.argv[3]

#convert to gif if not already 
if not ".gif" in image_name:
	os.system("rm -f /tmp/tmp.gif")
	os.system('ffmpeg  -i {} -vf "fps=10,scale=780:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 /tmp/tmp.gif'.format(image_name))
	image_name = "/tmp/tmp.gif"

#open images
background = Image.open("bg.png")
phone = Image.open("phone.png")
im = Image.open(image_name)

#loop over gif
frames = []
for frame in ImageSequence.Iterator(im):

		#copy background
		new_frame = background.copy()

		#crop status bar
		if status_cut > 0:
			w, h = frame.size
			frame = frame.crop((0,status_cut, w,h))

		#paste screen and phone over it
		new_frame.paste(frame,SCREEN_POS)
		new_frame.paste(phone,PHONE_POS, phone)

		#save modified image in the new gif
		b = io.BytesIO()
		new_frame.save(b, format="GIF")                                       
		new_frame = Image.open(b)
		frames.append(new_frame)

out = sys.argv[2]
frames[0].save(out, save_all=True, append_images=frames[1:],loop=0)