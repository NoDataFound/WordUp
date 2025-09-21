import io
import os
import logging
import numpy as np
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator
from utils import (
    ensure_dir,
    safe_join,
    upscale_to_4k_canvas,
    clean_text,
    recolor_image,
    add_background,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)

st.set_page_config(page_title="WordUp - Words into things", layout="wide")

DEFAULT_FONTS = {
    "Hacker": "assets/fonts/Hacker.ttf",
    "OpenSans": "assets/fonts/OpenSans.ttf",
    "Rushin": "assets/fonts/rushin.ttf",
}

DEFAULTS = {
    "max_words": 100000,
    "max_font_size": 175,
    "random_state": 42,
    "relative_scaling": 0.0,  

    "resize_step": 3,         
    "sigma": 2.0,             
    "edge_threshold": 0.08,   

    "recolor_from_image": True,

    "bundled_choices": ["Hacker", "OpenSans", "Rushin"],
    "font_pick": "Hacker",    

    "removals_raw": "",
    "use_regex": False,
    "ignore_case": True,
}


for k, v in [
    ("text_items", []),
    ("image_item", None),
    ("last_output", None),
    ("last_output_mod", None),
    ("last_output_4k", None),
    ("last_output_4k_mod", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v
    if "paste_nonce" not in st.session_state:
        st.session_state.paste_nonce = 0

def discover_texts(roots=("source_text", "assets")):
    exts = (".txt",)
    found = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if fn.lower().endswith(exts):
                    found.append(os.path.join(dirpath, fn))
    return sorted(set(found), key=lambda p: (os.path.basename(p).lower(), p.lower()))

def discover_gallery(root="assets"):
    exts = (".png", ".jpg", ".jpeg")
    found = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(exts):
                found.append(os.path.join(dirpath, fn))
    uniq = sorted(set(found), key=lambda p: os.path.basename(p).lower())
    placeholder = [p for p in uniq if os.path.basename(p).lower().startswith("wordup")]
    rest = [p for p in uniq if p not in placeholder]
    return placeholder + rest

def reset_section(keys):
    for k in keys:
        if k in DEFAULTS:
            st.session_state[k] = DEFAULTS[k]

st.sidebar.image("https://raw.githubusercontent.com/NoDataFound/WordUp/refs/heads/streamlit/streamlit_wordup/assets/wordup.png")

def _add_paste_to_pool():
    buf = st.session_state.get("paste_buffer", "").strip()
    if buf:
        st.session_state.text_items.append(buf)
    st.session_state["paste_buffer"] = ""


# Sidebar controls
with st.sidebar:
    with st.expander("Parameters", expanded=True):
        max_words = st.slider(
            "max_words",
            100, 300000,
            key="max_words",
            value=st.session_state.get("max_words", DEFAULTS["max_words"]),
            step=500,
        )
        max_font_size = st.slider(
            "max_font_size",
            16, 512,
            key="max_font_size",
            value=st.session_state.get("max_font_size", DEFAULTS["max_font_size"]),
            step=1,
        )
        random_state = st.number_input(
            "random_state",
            min_value=0,
            key="random_state",
            value=st.session_state.get("random_state", DEFAULTS["random_state"]),
            step=1,
        )
        relative_scaling = st.slider(
            "relative_scaling",
            0.0, 2.0,
            key="relative_scaling",
            value=st.session_state.get("relative_scaling", DEFAULTS["relative_scaling"]),
            step=0.05,
        )
        if st.button("Reset defaults - Parameters", width='stretch'):
            reset_section(["max_words", "max_font_size", "random_state", "relative_scaling"])
            st.experimental_rerun()

    with st.expander("Mask and Edge", expanded=True):
        resize_step = st.selectbox(
            "downsample factor",
            options=[1, 2, 3, 4],
            key="resize_step",
            index=[1,2,3,4].index(st.session_state.get("resize_step", DEFAULTS["resize_step"]))
        )
        sigma = st.slider(
            "gaussian sigma",
            0.0, 8.0,
            key="sigma",
            value=st.session_state.get("sigma", DEFAULTS["sigma"]),
            step=0.1,
        )
        edge_threshold = st.slider(
            "edge threshold",
            0.0, 0.5,
            key="edge_threshold",
            value=st.session_state.get("edge_threshold", DEFAULTS["edge_threshold"]),
            step=0.01,
        )
        if st.button("Reset defaults - Mask and Edge", width='stretch'):
            reset_section(["resize_step", "sigma", "edge_threshold"])
            st.experimental_rerun()

    with st.expander("Coloring", expanded=True):
        recolor_from_image = st.checkbox(
            "recolor using image colors",
            key="recolor_from_image",
            value=st.session_state.get("recolor_from_image", DEFAULTS["recolor_from_image"]),
        )
        if st.button("Reset defaults - Coloring", width='stretch'):
            reset_section(["recolor_from_image"])
            st.experimental_rerun()

    with st.expander("Font selection", expanded=True):
        bundled_choices = st.multiselect(
            "choose bundled fonts to enable",
            options=list(DEFAULT_FONTS.keys()),
            key="bundled_choices",
            default=st.session_state.get("bundled_choices", DEFAULTS["bundled_choices"]),
        )
        uploaded_font = st.file_uploader("or upload a font", type=["ttf", "otf"])
        font_pick = st.selectbox(
            "active font",
            options=bundled_choices + (["Uploaded"] if uploaded_font else []),
            key="font_pick",
            index=0 if bundled_choices else 0
        )

        def resolve_font_path():
            if font_pick == "Uploaded" and uploaded_font is not None:
                tmp_path = safe_join("assets", "fonts", "_session_font.ttf")
                ensure_dir(safe_join("assets", "fonts"))
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_font.read())
                return tmp_path
            if font_pick in DEFAULT_FONTS:
                return DEFAULT_FONTS[font_pick]
            return None

        font_path = resolve_font_path()

        if st.button("Reset defaults - Font selection", width='stretch'):
            reset_section(["bundled_choices", "font_pick"])
            st.experimental_rerun()

    with st.expander("Text cleaning", expanded=True):
        removals_raw = st.text_area(
            "remove these (one per line)",
            key="removals_raw",
            value=st.session_state.get("removals_raw", DEFAULTS["removals_raw"]),
            height=120,
            placeholder="Examples:\n@\nhttp://\nhttps://\nSecKC\n,  .  ;  :"
        )
        use_regex = st.checkbox(
            "treat patterns as regular expressions",
            key="use_regex",
            value=st.session_state.get("use_regex", DEFAULTS["use_regex"]),
        )
        ignore_case = st.checkbox(
            "ignore case",
            key="ignore_case",
            value=st.session_state.get("ignore_case", DEFAULTS["ignore_case"]),
        )
        if st.button("Reset defaults - Text cleaning", width='stretch'):
            reset_section(["removals_raw", "use_regex", "ignore_case"])
            st.experimental_rerun()

# Main two columns for inputs
left_col, right_col = st.columns(2, gap="small")

with left_col:
    st.success("Image input")

    img_upload = st.file_uploader(
        "Upload image",
        type=["png", "jpg", "jpeg"],
        key="img_up"
    )
    #st.caption("Drag and drop up to 200 MB • PNG, JPG, JPEG")

    if img_upload is not None:
        try:
            img = Image.open(img_upload).convert("RGBA")
            st.session_state.image_item = img
        except Exception as e:
            st.error(f"Image load error: {e}")

    if st.session_state.image_item is not None:
        st.image(
            st.session_state.image_item,
            #caption="Mask source",
            width='stretch'
        )
    else:
        pass
        #st.info("Upload an image to continue.")



with right_col:
    st.info("Text input")

    t_up, t_paste = st.columns([2, 3], gap="small")

    with t_up:
        text_uploads = st.file_uploader(
            "Upload text file(s)",
            type=["txt"],
            accept_multiple_files=True,
            key="txt_up_multi"
        )
        #st.caption("Drag and drop. TXT only.")

    with t_paste:
        ta_key = f"paste_buffer_{st.session_state.paste_nonce}"
        st.text_area(
            "Or paste text",
            height=187,
            placeholder="Paste text here",
            key=ta_key,
        )

    if st.button("Add to text pool", width='stretch'):
        if text_uploads:
            texts = []
            for f in text_uploads:
                try:
                    texts.append(f.read().decode("utf-8", errors="ignore"))
                except Exception as e:
                    st.warning(f"Failed to read {f.name}: {e}")
            if texts:
                st.session_state.text_items.extend(texts)

        pasted = st.session_state.get(ta_key, "").strip()
        if pasted:
            st.session_state.text_items.append(pasted)
            st.session_state.paste_nonce += 1

    # Preview
    if st.session_state.text_items:
        full_text = "\n".join(st.session_state.text_items)
        word_count = len(full_text.split())

        st.caption(f"Text pool preview ({word_count:,} words)")

        current_max_words = st.session_state.get("max_words", DEFAULTS["max_words"])
        if word_count > current_max_words:
            st.session_state.max_words = word_count
            st.toast(f"'max_words' auto-adjusted to {word_count}", icon="✅")

        st.code(full_text[:250] + ("..." if len(full_text) > 250 else ""))

        with st.expander("Manage text pool", expanded=False):
            st.caption("Edit or clear the text you’ve collected.")

            pool_edit = st.text_area(
                "Edit text pool",
                value="\n\n---\n\n".join(st.session_state.text_items),
                height=200,
                key="pool_editor",
            )

            c1, c2 = st.columns(2, gap="small")

            with c1:
                if st.button("Save edits", width='stretch'):
                    pieces = [p.strip() for p in pool_edit.split("\n\n---\n\n") if p.strip()]
                    st.session_state.text_items = pieces
                    st.success("Text pool updated")

            with c2:
                if st.button("Clear pool", width='stretch'):
                    st.session_state.text_items = []
                    st.session_state.paste_nonce = 0
                    st.info("Text pool cleared")
    else:
        pass
        #st.info("Your text pool is empty. Upload or paste to continue.")



run_button = st.button("WordUp", type="primary", width='stretch')

def build_mask_and_colors(img_rgba, step, sigma_val, thr):
    arr = np.array(img_rgba)
    arr = arr[::step, ::step, :]
    color_array = arr[:, :, :3].copy()
    mask = color_array.copy()
    mask[mask.sum(axis=2) == 0] = 255
    edges = np.mean(
        [gaussian_gradient_magnitude(color_array[:, :, i] / 255.0, sigma_val) for i in range(3)],
        axis=0
    )
    mask[edges > thr] = 255
    return color_array, mask

def generate_wordcloud(text, img_rgba):
    color_array, mask = build_mask_and_colors(img_rgba, resize_step, sigma, edge_threshold)

    wc = WordCloud(
        font_path=font_path,
        font_step=1,
        max_words=max_words,
        mask=mask,
        max_font_size=max_font_size,
        random_state=int(random_state),
        relative_scaling=relative_scaling,
        mode="RGBA",
        background_color=None,
        margin=0
    )

    wc.generate(text)

    if recolor_from_image:
        canvas_width, canvas_height = wc.width, wc.height
        color_source_img = Image.fromarray(color_array)
        resized_color_img = color_source_img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        final_color_array = np.array(resized_color_img)
        img_colors = ImageColorGenerator(final_color_array)
        wc.recolor(color_func=img_colors)

    return wc.to_image()

if run_button:
    if not st.session_state.image_item:
        st.error("please select or upload an image")
    elif not st.session_state.text_items:
        st.error("please upload or paste text")
    elif not font_path:
        st.error("please select or upload a font")
    else:
        try:
            full_text = "\n".join(st.session_state.text_items)

            removal_list = [line for line in removals_raw.splitlines() if line.strip() != ""]
            cleaned_text, removed_count = clean_text(
                full_text,
                removal_list,
                use_regex=use_regex,
                ignore_case=ignore_case
            )

            #with st.expander("cleaning summary", expanded=False):
            #    st.write(f"patterns applied: {len(removal_list)}")
            #    st.write(f"characters removed: {removed_count}")

            out_img = generate_wordcloud(cleaned_text, st.session_state.image_item)
            st.session_state.last_output = out_img
            st.session_state.last_output_mod = out_img.copy()

            out_4k = upscale_to_4k_canvas(out_img)
            st.session_state.last_output_4k = out_4k
            st.session_state.last_output_4k_mod = out_4k.copy()

            #st.success("generated")
        except Exception as e:
            logging.exception("generation failure")
            st.error(f"error: {e}")

if st.session_state.last_output is not None and st.session_state.last_output_4k is not None:
    #col_a, col_b = st.columns(2, gap="large")

    #with col_a:
    #    st.subheader("Result")
    #    st.image(st.session_state.last_output_mod, caption="generated wordcloud", width='stretch')
#
    #    with st.expander("Add background and recolor", expanded=False):
    #        add_bg_a = st.checkbox("add background to Result", key="add_bg_a", value=False)
    #        bg_color_a = st.color_picker("background color", "#000000", key="bg_color_a")
    #        recolor_a = st.checkbox("recolor image", key="recolor_a", value=False)
    #        tint_color_a = st.color_picker("tint color", "#FF00FF", key="tint_color_a")
    #        tint_strength_a = st.slider("tint strength", 0.0, 1.0, 0.35, 0.05, key="tint_strength_a")
#
    #        if st.button("Apply to Result", width='stretch'):
    #            img = st.session_state.last_output.copy()
    #            if recolor_a:
    #                img = recolor_image(img, tint_color_a, tint_strength_a)
    #            if add_bg_a:
    #                img = add_background(img, bg_color_a)
    #            st.session_state.last_output_mod = img
#
    #    buf = io.BytesIO()
    #    st.session_state.last_output_mod.save(buf, format="PNG")
    #    st.download_button(
    #        "download PNG",
    #        data=buf.getvalue(),
    #        file_name="wordcloud.png",
    #        mime="image/png",
    #        width='stretch'
    #    )

    #with col_b:
    st.caption("3840 by 2160 PNG canvas")
    st.image(st.session_state.last_output_4k_mod, width='stretch')
    with st.expander("Add background and recolor", expanded=False):
        add_bg_b = st.checkbox("add background to 4K", key="add_bg_b", value=False)
        bg_color_b = st.color_picker("background color", "#000000", key="bg_color_b")
        recolor_b = st.checkbox("recolor 4K image", key="recolor_b", value=False)
        tint_color_b = st.color_picker("tint color", "#FF00FF", key="tint_color_b")
        tint_strength_b = st.slider("tint strength", 0.0, 1.0, 0.35, 0.05, key="tint_strength_b")
        if st.button("Apply to 4K", width='stretch'):
            img4k = st.session_state.last_output_4k.copy()
            if recolor_b:
                img4k = recolor_image(img4k, tint_color_b, tint_strength_b)
            if add_bg_b:
                img4k = add_background(img4k, bg_color_b)
            st.session_state.last_output_4k_mod = img4k
    buf4k = io.BytesIO()
    st.session_state.last_output_4k_mod.save(buf4k, format="PNG")
    st.download_button(
        "download 4K PNG",
        data=buf4k.getvalue(),
        file_name="wordcloud_4k.png",
        mime="image/png",
        width='stretch'
    )
