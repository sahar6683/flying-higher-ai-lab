PROJECT AGRITECH DECISION BENCHMARK - INTERACTIVE AUDIT PAGE

FILES
  index.html   the page (no editing needed)
  data.csv     all the numbers; edit this to update the page
  images/      put your 40 original photos here

IMAGES
  Names must match the image_filename column in data.csv, e.g. "img_clean (1).JPG".
  Missing images show a placeholder automatically. Upper/lower-case extension
  (.JPG / .jpg) is tried both ways, but the rest of the name must match exactly.
  Tip: resize photos to about 1200 px on the long side so the page loads fast on phones.

UPDATING DATA (latency / cost)
  1. Fix the numbers in the Excel master sheet.
  2. Export it as CSV (UTF-8) with the same column names and replace data.csv.
     Do not export the formula columns (G_total_lat_ms, Jev_total_lat_ms, *_api_success);
     the page adds up totals itself from the four per-primitive latencies.
  3. Upload data.csv. No other change needed. Refresh the page.
  Cost/tokens: leave blank or 0 and the page shows "not recorded".
  Jev_box_coords is read as [top, left, bottom, right] on a 0-1000 scale (to be confirmed).

HOSTING
  Upload all three items to any static web host, keeping them in the same folder.
  Opening index.html by double-click will NOT load the data (browser security).
  To test locally:  python3 -m http.server   then open http://localhost:8000
  Direct link to one image: index.html#img-3
