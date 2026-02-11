# Quick Start: Alfred Vision Features

## TL;DR

Alfred can now **see and analyze** images! 🎉

### What Changed?

**Old Way:**
```
IMG_1234.jpg → photo_1234.jpg  (based on filename)
```

**New Way (Vision):**
```
IMG_1234.jpg → [AI looks at image] → golden_retriever_playing.jpg
```

---

## How to Use

### Option 1: Via UI (macOS App)

1. **Rename Images:**
   - Click Alfred icon → Select "Rename"
   - Choose image file(s)
   - Click "Preview Renames"
   - Alfred analyzes image content with vision
   - Click "Confirm" to apply

2. **Organize Images:**
   - Click Alfred icon → Select "Organize"
   - Choose folder with images
   - Click "Preview Plan"
   - Alfred groups by content (Nature, People, etc.)
   - Click "Confirm" to organize

### Option 2: Via CLI

```bash
cd /Users/aryangosaliya/Desktop/Alfred/cli
source venv/bin/activate

# Rename images (preview)
python alfred.py rename ~/Pictures/*.jpg

# Rename images (execute)
python alfred.py rename ~/Pictures/*.jpg --confirm

# Organize folder (preview)
python alfred.py organize ~/Downloads

# Organize with instructions
python alfred.py organize ~/Downloads --instructions "group vacation photos"

# Execute organization
python alfred.py organize ~/Downloads --confirm
```

---

## Real Example

```bash
$ python alfred.py rename "Gemini_Generated_Image_fr8zzgfr8zzgfr8z (1).png"

Analyzing 1 image(s) with vision...

Plan:
  Gemini_Generated_Image_fr8zzgfr8zzgfr8z (1).png → twins_automotive_flyer.png

Preview only. Use --confirm to execute.
```

Alfred **looked at the image**, saw it was an automotive flyer, and suggested a descriptive name!

---

## What Alfred Can See

- Objects in images (people, animals, vehicles, etc.)
- Scenes (nature, urban, indoor, outdoor)
- Text in images (signs, documents, screenshots)
- Image type (photos, screenshots, flyers, memes)
- Content themes (vacation, work, food, etc.)

---

## Supported Image Formats

✅ JPEG, PNG, GIF, WebP, BMP

---

## Current AI Configuration

```env
AI_PROVIDER=gemini
AI_MODEL=gemini/gemini-2.5-flash
GOOGLE_API_KEY=AIzaSyBf-vPYNzwCK82F5PXRpAa25a7wFPEWGjs
```

---

## Cost

**Very affordable:**
- ~$0.002 per image (~0.2 cents)
- 100 images = ~$0.20 (20 cents)

---

## Tips

1. **Use specific instructions** for better results:
   - "organize vacation photos from Italy trip"
   - "rename screenshots from work project"
   - "group family photos"

2. **Limit batch sizes** for faster processing:
   - Rename processes 5 images at a time
   - Organize analyzes 10 images per request

3. **Preview first!**
   - Always check the preview before confirming
   - Vision AI is smart but not perfect

---

## Troubleshooting

**Vision not working?**
1. Check you're using a vision-capable model (Gemini 2.5 Flash ✅)
2. Check API key is valid
3. Make sure files are actual images (not renamed documents)

**No "Confirm" button in UI?**
1. Make sure you ran "Preview" first
2. Check logs for "Plan:" or "preview" message
3. Restart Alfred app if needed

---

## Need Help?

- **Documentation:** See `VISION_UPDATE.md` for full details
- **GitHub Issues:** https://github.com/Aryanag2/Alfred/issues
- **Configuration:** Check `cli/.env` file

---

Enjoy smarter file management with Alfred Vision! 🚀
