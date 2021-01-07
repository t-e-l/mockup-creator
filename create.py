from PIL import Image, ImageDraw, ImageSequence
import io, sys, os
#use like : python gif2mock.py [my.gif/my.mp4] out 48


#https://stackoverflow.com/a/11291419
def add_corners (im, rad):
    circle = Image.new ('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw (circle)
    draw.ellipse ((0, 0, rad * 2, rad * 2), fill = 255)
    alpha = Image.new ('L', im.size, 255)
    w, h = im.size
    alpha.paste (circle.crop ((0, 0, rad, rad)), (0, 0))
    alpha.paste (circle.crop ((0, rad, rad, rad * 2)), (0, h-rad))
    alpha.paste (circle.crop ((rad, 0, rad * 2, rad)), (w-rad, 0))
    alpha.paste (circle.crop ((rad, rad, rad * 2, rad * 2)), (w-rad, h-rad))
    im.putalpha (alpha)
    return im


#positions to paste screen and phone
SCREEN_POS = (257,295)
PHONE_POS = (248,270)
LOGO_POS = (217,0)

output_webm = "output/{}.webm".format(sys.argv[2])
output_mp4 = "output/{}.mp4".format(sys.argv[2])
image_name = sys.argv[1]
status_cut = 48
if len(sys.argv) > 3:
	status_cut = int(sys.argv[3])
#convert to gif if not already 
if not ".gif" in image_name:
	print("=> converting your input to gif first")
	#scaling to 780 width to fit template
	#for other heights adjust cutout value
	os.system('ffmpeg -i {} -vf "fps=10,scale=780:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 /tmp/tmp.gif -y'.format(image_name))
	image_name = "/tmp/tmp.gif"

#open images
background = Image.open("bg.png")
phone = Image.open("phone.png")
logo = Image.open("logo.png")
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
	#cut round corners of the screen
	frame = add_corners(frame.convert("RGBA"),50)
	#paste screen, over it phone
	new_frame.paste(frame,SCREEN_POS,frame)
	new_frame.paste(phone,PHONE_POS, phone)
	new_frame.paste(logo,LOGO_POS,logo)
	#save modified frame
	frames.append(new_frame)

#save gif		
frames[0].save("/tmp/tmp2.gif", save_all=True, append_images=frames[1:],loop=0)

#save webm and mp4
os.system("ffmpeg -i /tmp/tmp2.gif -an -c vp9 -b:v 0 -crf 20 -pass 1 -f webm /dev/null -y")
os.system("ffmpeg -i /tmp/tmp2.gif -an -c vp9 -b:v 0 -crf 20 -pass 2 {} -y".format(output_webm))
os.system("ffmpeg -i {} -c copy /tmp/tmp.mp4 -y".format(output_webm,output_mp4))

#extract first frame and set thumbnail
os.system('ffmpeg -i /tmp/tmp2.gif -vf "select=eq(n\,0)" -q:v 3 /tmp/thumbnail.png -y')
os.system('ffmpeg -i /tmp/tmp.mp4 -i /tmp/thumbnail.png -map 1 -map 0 -c copy -disposition:0 attached_pic {0} -y '.format(output_mp4))
