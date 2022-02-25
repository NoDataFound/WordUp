#source text from: hxxp://kremlin[.]ru/events/president/news/67843
import os
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator

d = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
text_path =  d + '/source_text/'
image_path =  d + '/source_images/'
output_path =  d + '/output/'
text = open(os.path.join(d, text_path + 'AjzMrDla0OA.txt'), encoding="utf-8").read()
source_color = np.array(Image.open(os.path.join(d, image_path + "ukraine.png")))
source_color = source_color[::3, ::3]
source_mask = source_color.copy()
source_mask[source_mask.sum(axis=2) == 0] = 255
edges = np.mean([gaussian_gradient_magnitude(source_color[:, :, i] / 255., 2) for i in range(3)], axis=0)
source_mask[edges > .08] = 255

#https://www.1001freefonts.com/rushin.font
#font_path = d + '/fonts/rushin/rushin.ttf'
#font_path = d + '/fonts/soviet-program/SovietProgram.ttf'
font_path = d + '/fonts/Open_Sans/static/OpenSans/OpenSans-Light.ttf'
#font_path = d + '/fonts/soviet/Soviet2.ttf'

source_mask = source_color.copy()
source_mask[source_mask.sum(axis=2) == 0] = 255
print('''
   ________  ________  ________   _______  ________  ________ 
  ╱  ╱  ╱  ╲╱        ╲╱        ╲_╱       ╲╱    ╱   ╲╱        ╲
 ╱         ╱         ╱         ╱         ╱         ╱         ╱
╱╱        ╱         ╱        _╱         ╱        ╱╱       __╱ 
╲╲_______╱╲________╱╲____╱___╱╲________╱╲_______╱╱╲______╱    
                                 I make words into things
''')
wc = WordCloud(font_path=font_path, max_words=4000, mask=source_mask, max_font_size=175,random_state=42, relative_scaling=0)

wc.generate(text)
image_colors = ImageColorGenerator(source_color)
wc.recolor(color_func=image_colors)
wc.to_file(output_path + "ukraine.png")
