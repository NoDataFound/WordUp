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
text = open(os.path.join(d, text_path + 'EN.02.24.22.Address.by.the.President.of.the.Russian.Federation.txt'), encoding="utf-8").read()
russia_color = np.array(Image.open(os.path.join(d, image_path + "russia.png")))
russia_color = russia_color[::3, ::3]
russia_mask = russia_color.copy()
russia_mask[russia_mask.sum(axis=2) == 0] = 255
edges = np.mean([gaussian_gradient_magnitude(russia_color[:, :, i] / 255., 2) for i in range(3)], axis=0)
russia_mask[edges > .08] = 255

#https://www.1001freefonts.com/rushin.font
#font_path = d + '/fonts/rushin/rushin.ttf'
#font_path = d + '/fonts/soviet-program/SovietProgram.ttf'
#font_path = d + '/fonts/Open_Sans/static/OpenSans/OpenSans-Light.ttf'
font_path = d + '/fonts/soviet/Soviet2.ttf'

russia_mask = russia_color.copy()
russia_mask[russia_mask.sum(axis=2) == 0] = 255
print('''
   ________  ________  ________   _______  ________  ________ 
  ╱  ╱  ╱  ╲╱        ╲╱        ╲_╱       ╲╱    ╱   ╲╱        ╲
 ╱         ╱         ╱         ╱         ╱         ╱         ╱
╱╱        ╱         ╱        _╱         ╱        ╱╱       __╱ 
╲╲_______╱╲________╱╲____╱___╱╲________╱╲_______╱╱╲______╱    
                                 I make words into things
''')
wc = WordCloud(font_path=font_path, max_words=4000, mask=russia_mask, max_font_size=175,random_state=42, relative_scaling=0)

wc.generate(text)
image_colors = ImageColorGenerator(russia_color)
wc.recolor(color_func=image_colors)
wc.to_file(output_path + "russia_speech_wordcloud.png")
