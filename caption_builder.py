# project/caption_builder.py
import re

def build_caption_units(data,
                        max_words_per_line=5,
                        max_words_per_caption=10,
                        continue_if_gap_ms=200,
                        separate_if_gap_ms=600):
    """
    Build caption units obeying precise pause rules.

    Rules (defaults):
      - gap < continue_if_gap_ms  => continue the same caption line
      - continue_if_gap_ms <= gap < separate_if_gap_ms => insert a line break in the same caption (natural new line)
      - gap >= separate_if_gap_ms => end/flush current caption (caption vanishes during gap) and start a new caption

    Preserves per-word timestamps and returns captions with:
      - 'start' (float seconds)
      - 'end' (float seconds)
      - 'text_ass' (lines separated by '\\N')
      - 'text_srt' (lines separated by '\n')
      - 'words' list of (word, start, end)
    """
    captions = []

    # convert thresholds to seconds
    cont_th = float(continue_if_gap_ms) / 1000.0
    sep_th = float(separate_if_gap_ms) / 1000.0

    def flush(curr):
        """Flush a current caption (list of (word, s, e) and line-break markers)."""
        if not curr:
            return
        # curr is list of tuples or markers representing words and '\n' linebreak placeholders
        # We will compress into lines by scanning curr for line-break markers
        lines = []
        cur_line = []
        start = None
        end = None
        words_for_meta = []
        for item in curr:
            if item == "__LINE_BREAK__":
                # push current line
                if cur_line:
                    lines.append(' '.join(cur_line))
                    cur_line = []
                continue
            # item is (word, s, e)
            w, s, e = item
            if start is None:
                start = float(s)
            end = float(e)
            cur_line.append(w)
            words_for_meta.append((w, float(s), float(e)))
        if cur_line:
            lines.append(' '.join(cur_line))

        if start is None or end is None:
            return

        captions.append({
            'start': float(start),
            'end': float(end),
            'text_ass': '\\\\N'.join(lines),
            'text_srt': '\\n'.join(lines),
            'words': words_for_meta
        })

    # determine if segments have per-word timestamps
    any_words = any('words' in seg and seg['words'] for seg in data.get('segments', []))
    if not any_words:
        # fallback: distribute segment timestamps evenly as older behavior
        current = []
        last_end = None
        for seg in data.get('segments', []):
            seg_text = seg.get('text', '').strip()
            if not seg_text:
                continue
            seg_start = float(seg.get('start', 0.0))
            seg_end = float(seg.get('end', seg_start))
            seg_words = [w for w in re.split(r"\s+", seg_text) if w]
            if not seg_words:
                continue
            per_word = (seg_end - seg_start) / max(1, len(seg_words))
            for i, w in enumerate(seg_words):
                s = seg_start + i * per_word
                e = s + per_word
                gap = 0 if last_end is None else s - last_end
                # Use same thresholds but approximate
                if gap >= sep_th or len([x for x in current if x != "__LINE_BREAK__"]) >= max_words_per_caption:
                    flush(current)
                    current = []
                # moderate gap -> line break inside caption
                if last_end is not None and cont_th <= gap < sep_th and current:
                    current.append("__LINE_BREAK__")
                current.append((w, s, e))
                last_end = e
        flush(current)
        return captions

    # With per-word timestamps:
    current = []
    last_end = None
    words_in_current = 0  # count of words (not counting line-break markers)
    for seg in data.get('segments', []):
        for w in seg.get('words', []):
            word_text = (w.get('word') or '').strip()
            if not word_text:
                continue
            try:
                w_start = float(w.get('start', 0.0))
                w_end = float(w.get('end', w_start))
            except Exception:
                continue

            gap = 0 if last_end is None else (w_start - last_end)

            # if gap >= separate threshold -> end current caption and start a new one
            if last_end is not None and gap >= sep_th:
                # flush current so it vanishes during gap
                flush(current)
                current = []
                words_in_current = 0

            # if adding this word would exceed max words per caption, flush and start new
            if words_in_current >= max_words_per_caption:
                flush(current)
                current = []
                words_in_current = 0

            # moderate gaps: insert a line-break marker inside the same caption
            if last_end is not None and cont_th <= gap < sep_th and current:
                # only insert if current line isn't already exhausted by max_words_per_line
                current.append("__LINE_BREAK__")

            # for very small gaps (< cont_th) -> we continue same line (no op)
            # add the word
            current.append((word_text, w_start, w_end))
            words_in_current += 1

            # enforce per-line maximum: if current line would exceed max_words_per_line, we insert line-break
            # count words since last line break
            # compute words since last line break
            rev = list(reversed(current))
            count_since_break = 0
            for it in rev:
                if it == "__LINE_BREAK__":
                    break
                count_since_break += 1
            if count_since_break >= max_words_per_line:
                # only insert break if we won't exceed caption word limit by doing so
                if words_in_current < max_words_per_caption:
                    current.append("__LINE_BREAK__")

            # strong punctuation heuristic: if the word ends a sentence, flush immediately
            if re.search(r'[\.!\?]$', word_text):
                flush(current)
                current = []
                words_in_current = 0

            last_end = w_end

    flush(current)
    return captions