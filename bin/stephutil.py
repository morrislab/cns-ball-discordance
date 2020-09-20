def find_samp_pairs(sampnames, tail1, tail2):
  pairs = []
  for idx1, samp in enumerate(sampnames):
    if not samp.endswith(tail1):
      continue
    other = samp[:-len(tail1)] + tail2
    if other not in sampnames:
      continue
    idx2 = sampnames.index(other)
    pairs.append((idx1, idx2))
  return pairs

