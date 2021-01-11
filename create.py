from PIL import Image, ImageDraw, ImageSequence, ImageFont
import io, sys, os, getopt
import pathlib


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


INPUT_FILE = "input.mp4"
OUTPUT_FILE = "output.mp4"
STATUS_CUT = 48
BACKGROUND_COLOR = "#1f1f1f"
VERBOOSE = "&>/dev/null"
URL="t-e-l.github.io"
VERSION="0.1"
#open images
background = Image.open("bg.png")
phone = Image.open("phone.png")
phone_top = Image.open("phone_top.png")
phone_mid = Image.open("phone_mid.png")
phone_bot = Image.open("phone_bot.png")
logo = Image.open("tel.png")


try:
  opts, args = getopt.getopt(sys.argv[1:],"i:o:c:b:v",["ifile=","ofile="])
except getopt.GetoptError:
  print ("wrong parameters")
  sys.exit(2)
for opt, arg in opts:
	if opt == "-i":
		INPUT_FILE = arg
	elif opt == "-o":
		OUTPUT_FILE = arg
	elif opt == "-c":
		STATUS_CUT = int(arg)
	elif opt == "-b":
		BACKGROUND_COLOR = arg
		if not "#" in BACKGROUND_COLOR:
			BACKGROUND_COLOR = "#{}".format(BACKGROUND_COLOR)
		if not BACKGROUND_COLOR == "#364a39":
			background = Image.new('RGBA', (1300, 2000), BACKGROUND_COLOR)
	elif opt == "-v":
		VERBOOSE = ""

print("=> input file: {}".format(INPUT_FILE))
print("=> output file: output/{}.mp4".format(OUTPUT_FILE))
print("=> status cut: {} px".format(STATUS_CUT))
print("=> background color: {}".format(BACKGROUND_COLOR))



pathlib.Path('tmp').mkdir(exist_ok=True) 
pathlib.Path('output').mkdir(exist_ok=True) 

#positions to paste screen and phone
SCREEN_POS = (257,295)
PHONE_POS = (248,270)
LOGO_POS = (217,0)

output_mp4 = "output/{}.mp4".format(OUTPUT_FILE)
image_name = INPUT_FILE
#convert to gif if not already 
if not ".gif" in image_name:
	print("=> converting input to gif")
	#scaling to 780 width to fit template
	#for other heights adjust cutout value
	os.system('ffmpeg -i {} -vf "fps=10,scale=780:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 tmp/tmp.gif -y {}'.format(image_name,VERBOOSE))
	image_name = "tmp/tmp.gif"


wl, hl = logo.size

if not wl == 865:
	LOGO_POS = (LOGO_POS[0]+int((865-wl)/2),LOGO_POS[1])

im = Image.open(image_name)
w, h = im.size


#dynamic phone template creation
real_size = h -STATUS_CUT
if not real_size == 1642:
	print("=> dynamically creating phone image")
	#recenter phone and screen
	diff = int((1642 -real_size)/2)
	SCREEN_POS=(SCREEN_POS[0],SCREEN_POS[1]+diff)
	PHONE_POS=(PHONE_POS[0],PHONE_POS[1]+diff)
	#create empty phone image
	phone = Image.new('RGBA', (804, real_size+50), (255, 0, 0, 0))
	#paste top part
	phone.paste(phone_top,(0,0),phone_top)
	#calculate how much middle parts
	middle_height = real_size -300


	count = int(middle_height / 50)+1
	if not middle_height % 50 == 0:
		count+=1
	y = 150
	#paste middle parts
	while count > 0:
		phone.paste(phone_mid,(0,y),phone_mid)
		count-=1
		y+=50
	#paste bottom parts over last middle part, so everything % 50 != works
	phone.paste(phone_bot,(0,real_size -100),phone_bot)
	#phone.save("test_phone.png", "PNG") todo: save phone image for reuse

print("=> creating gif")
#loop over gif
frames = []
first_frame = None
for frame in ImageSequence.Iterator(im):
	#copy background
	new_frame = background.copy()
	#crop status bar
	if STATUS_CUT > 0:
		w, h = frame.size
		frame = frame.crop((0,STATUS_CUT, w,h))
	#cut round corners of the screen
	frame = add_corners(frame.convert("RGBA"),80)
	#paste screen, over it phone
	new_frame.paste(frame,SCREEN_POS,frame)
	new_frame.paste(phone,PHONE_POS, phone)
	new_frame.paste(logo,LOGO_POS,logo)
	draw = ImageDraw.Draw(new_frame)
	font = ImageFont.truetype("font.ttf", 50)
	font2 = ImageFont.truetype("font.ttf",120)
	version_str = "v{}".format(VERSION)
	textw, texth = draw.textsize(version_str,font)
	textw2, texth2 = draw.textsize(URL,font2)
	w, h = new_frame.size
	draw.text((w-textw, 5),version_str,"#c0b18b",font=font)
	#save modified frame

	img_txt = Image.new('RGBA', (h,w), (255,255,255,0))
	draw_txt = ImageDraw.Draw(img_txt)
	draw_txt.text(((h-(textw2))/2,240-texth2), URL, font=font2, fill="#c0b18b")
	#draw_txt.text((0, 0), URL,(192, 177, 139,80),font=font2)
	t = img_txt.rotate(90, expand=1)
	#txt = Image.new('RGBA', new_frame.size, (255,255,255,0))
	#d = ImageDraw.Draw(txt)    
	#d.text((200, h-250),URL,(192, 177, 139,80),font=font2, stroke=10,stroke_color=(0, 0, 0))
	new_frame = Image.alpha_composite(new_frame, t)    
	if first_frame == None:
		first_frame = new_frame
	frames.append(new_frame)
#save gif		
frames[0].save("tmp/tmp2.gif", save_all=True, append_images=frames[1:],loop=0)

print("=> creating mp4")
#save webm
os.system('ffmpeg -i tmp/tmp2.gif -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" {} -y {}'.format(output_mp4,VERBOOSE))


#first_frame.save("tmp/thumbnail.png")
#os.system('ffmpeg -i tmp/tmp.mp4 -i tmp/thumbnail.png -map 0 -map 1 -c copy -c:v:1 png -disposition:v:1 attached_pic {} -y {}'.format(output_mp4,VERBOOSE))

print("=> done!")
