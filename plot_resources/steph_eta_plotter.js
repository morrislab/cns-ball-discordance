function StephEtaPlotter() {
  this._col_width = 50;
  this._col_height = 500;
  this._legend_spacing = 60;
  this._font_size = 16;
  this._legend_font_size = 14;
  this._label_padding = 10;
  this._legend_splotch_size = 30;
  this._legend_padding = 5;
  this._legend_splotch_spacing = 20;
  this._col_space = 5;
  this._discord_height = 50;
  this._discord_spacing = 10;
  this._discord_legend_width = this._legend_splotch_size;
}

StephEtaPlotter.prototype._calc_label_width = function(labels) {
  var max_length = 0;
  var char_width = 15;
  for(let label of labels) {
    if(label.length > max_length) {
      max_length = label.length;
    }
  }
  return char_width * max_length;
}

StephEtaPlotter.prototype._calc_cum_on_axis0 = function(mat) {
  var K = mat.length;
  var S = mat[0].length;
  var S_range = Array.from(Array(S).keys());

  var cum = [S_range.map(d => 0)];
  for(let k = 1; k < K; k++) {
    cum.push(S_range.map(s => cum[k - 1][s] + mat[k - 1][s]));
  }
  return cum;
}

StephEtaPlotter.prototype._calc_cum = function(A) {
  let cum = [0];
  for(var idx = 1; idx < A.length; idx++) {
    cum.push(cum[idx - 1] + A[idx - 1]);
  }
  return cum;
}

StephEtaPlotter.prototype._plot_etas = function(svg, eta, samp_labels, col_widths, col_spacing, pop_colours, col_label_height) {
  let self = this;
  let K = eta.length;
  let S = eta[0].length;
  let K_range = Array.from(Array(K).keys());
  let S_range = Array.from(Array(S).keys());
  let eta_cum = this._calc_cum_on_axis0(eta);
  let cum_col_spacing = this._calc_cum(col_spacing);
  let cum_col_widths = this._calc_cum(col_widths);

  if(samp_labels.length !== S) {
    throw "Wrong number of samp labels";
  }

  let cl = svg.append('svg:g')
    .attr('class', 'col_labels')
    .attr('transform', 'translate(0,' + (col_label_height - self._label_padding) + ')')
    .selectAll('text')
    .data(samp_labels)
    .join('svg:text')
    .attr('transform', function(d, i) { return 'translate(' + (0.5*col_widths[i] + cum_col_widths[i] + cum_col_spacing[i]) + ',0) rotate(270)'; })
    .attr('x', 0)
    .attr('y', 0)
    .attr('font-size', this._font_size)
    .attr('font-weight', 'bold')
    .text(function(d, i) { return d; });

  let cols = svg.append('svg:g')
    .attr('class', 'cols')
    .attr('transform', 'translate(0,' + (self._discord_height + self._discord_spacing + col_label_height) + ')')
    .selectAll('g.col')
    .data(S_range)
    .join('svg:g')
    .attr('class', 'col')
    .attr('transform', function(d, i) {
      return 'translate(' + (cum_col_widths[i] + cum_col_spacing[i]) + ',0)';
    });

  cols.selectAll('rect')
    .data(function(sidx) { return K_range.map(function(k) { return {k: k, s: sidx}; }); })
    .join('svg:rect')
    .attr('width', d => col_widths[d.s])
    .attr('height', function(d) { return eta[d.k][d.s] * self._col_height; })
    .attr('x', 0)
    .attr('y', function(d, i) { return eta_cum[d.k][d.s] * self._col_height; })
    .attr('fill-opacity', function(d) { return 1.0; })
    .attr('fill', function(d, i) { return pop_colours[i]; });
}

StephEtaPlotter.prototype._add_pop_legend = function(svg, pop_labels, pop_colours, x_offset, y_offset) {
  let self = this;
  let legend = svg.append('svg:g')
    .attr('transform', 'translate(' + x_offset + ',' + y_offset + ')')
    .selectAll('g.label')
    .data(pop_labels)
    .join('svg:g')
    .attr('transform', function(d, i) { return 'translate(0,' + i*self._legend_splotch_size + ')'; })
    .attr('class', 'label');
  legend
    .append('svg:rect')
    .attr('width', this._legend_splotch_size)
    .attr('height', this._legend_splotch_size)
    .attr('x', 0)
    .attr('y', -0.5*this._legend_splotch_size)
    .attr('fill-opacity', 1.0)
    .attr('fill', function(d, i) { return pop_colours[i]; });
  legend
    .append('svg:text')
    .attr('font-size', this._legend_font_size)
    .attr('x', this._legend_splotch_size + this._legend_padding)
    .attr('dominant-baseline', 'central')
    .text(function(d) { return d; });
}

StephEtaPlotter.prototype._remove_small_pops = function(eta, pop_labels, threshold) {
  let K = eta.length;
  let S = eta[0].length;

  for(let k = K - 1; k >= 0; k--) {
    let remove_k = true;
    for(let s = 0; s < S; s++) {
      if(eta[k][s] >= threshold) {
        remove_k = false;
        break;
      }
    }
    if(remove_k) {
      eta.splice(k, 1);
      pop_labels.splice(k, 1);
    }
  }
}

StephEtaPlotter.prototype._find_discord_pairs = function(samp_labels, discord) {
  let pairs = [];

  for(let s = 0; s < samp_labels.length - 1; s++) {
    let slabel1 = samp_labels[s];
    let slabel2 = samp_labels[s+1];

    for(let d = 0; d < discord.length; d++) {
      if(discord[d][0] === slabel1 && discord[d][1] === slabel2) {
        pairs.push({
          sidx1: s,
          sidx2: s+1,
          p_discord: discord[d][2],
        });
        break;
      }
    }
  }

  return pairs;
}

StephEtaPlotter.prototype._make_col_spacing = function(S, discord_pairs, col_widths) {
  let col_spacing = [];
  let big_col_space = 4*this._col_space;
  let cum_col_widths = this._calc_cum(col_widths);

  for(let s = 0; s < S - 1; s++) {
    let is_pair = false;
    for(let d = 0; d < discord_pairs.length; d++) {
      if(discord_pairs[d].sidx1 === s && discord_pairs[d].sidx2 === s+1) {
        is_pair = true;
        break;
      }
    }
    col_spacing.push(is_pair ? this._col_space : big_col_space);
  }

  // Leave no space after last column.
  col_spacing.push(0);
  return col_spacing;
}

StephEtaPlotter.prototype._plot_discord = function(svg, discord_pairs, col_label_height, col_widths, col_spacing, colour) {
  let cum_col_width = this._calc_cum(col_widths);
  let cum_col_spacing = this._calc_cum(col_spacing);

  for(let d = 0; d < discord_pairs.length; d++) {
    let s1 = discord_pairs[d].sidx1;
    let s2 = discord_pairs[d].sidx2;
    discord_pairs[d].x_offset = cum_col_width[s1] + cum_col_spacing[s1];
    discord_pairs[d].width = col_widths[s1] + col_widths[s2] + col_spacing[s1];
  }

  let elems = svg.append('svg:g')
    .attr('class', 'discord_bars')
    .attr('transform', 'translate(0,' + col_label_height + ')')
    .selectAll('rect')
    .data(discord_pairs)
    .join('svg:rect')
    .attr('x', d => d.x_offset)
    .attr('y', 0)
    .attr('width', d => d.width)
    .attr('height', this._discord_height)
    .attr('fill', d => colour(d.p_discord));
}

StephEtaPlotter.prototype._ramp = function(colour, n = 256) {
  const canvas = d3.create('canvas')
    .attr('width', 1)
    .attr('height', n)
    .node();
  const context = canvas.getContext("2d");
  for (let i = 0; i < n; ++i) {
    context.fillStyle = colour(i / (n - 1));
    context.fillRect(0, i, 1, 1);
  }
  return canvas;
}

StephEtaPlotter.prototype._make_discord_legend = function(svg, colour, x_offset, y_offset) {
  let scale = d3.scaleSequential([0, 100], colour);

  let legend = svg.append('svg:g')
    .attr('class', 'discord_legend')
    .attr('transform', 'translate(' + x_offset + ',' + y_offset + ')');
  legend.append('image')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', this._discord_legend_width)
    .attr('height', this._discord_height)
    .attr('preserveAspectRatio', 'none')
    .attr('xlink:href', this._ramp(scale.interpolator()).toDataURL());

  let axis_scale = d3.scaleLinear()
    .domain([0, 1])
    .range([0, this._discord_height]);
  legend.append('g')
    .attr('transform', 'translate(' + (this._discord_legend_width + this._legend_padding) + ',0)')
    .call(d3.axisRight(axis_scale)
      .ticks(1)
      .tickSize(5)
      .tickFormat(t => t < 0.5 ? 'Concordant' : 'Discordant')
    ).call(g => g.selectAll('text').attr('font-size', this._legend_font_size));
}

StephEtaPlotter.prototype._renormalize_eta = function(eta) {
  let K = eta.length;
  let S = eta[0].length;

  for(let s = 0; s < S; s++) {
    let eta_s_sum = eta.reduce((sum, cur) => sum + cur[s], 0);
    for(let k = 0; k < K; k++) {
      eta[k][s] /= eta_s_sum;
    }
  }
}

StephEtaPlotter.prototype.plot = function(eta, samp_labels, discord, container, remove_small_pop_threshold=0.01, remove_pop0=false) {
  let self = this;
  let pop_labels =  Array.from(Array(eta.length).keys()).map(idx => 'Pop. ' + idx);
  if(remove_pop0) {
    eta = eta.slice(1);
    pop_labels = pop_labels.slice(1);
  }
  if(remove_small_pop_threshold > 0) {
    this._remove_small_pops(eta, pop_labels, remove_small_pop_threshold);
  }
  this._renormalize_eta(eta);

  let K = eta.length;
  let S = eta[0].length;
  let K_range = Array.from(Array(K).keys());
  let S_range = Array.from(Array(S).keys());

  let pop_colours = ColourAssigner.assign_colours(K);
  let pop_label_width = this._calc_label_width(pop_labels);
  let col_label_height = this._calc_label_width(samp_labels);

  let col_widths = samp_labels.map(label => (label.indexOf('Xeno') > -1 ? self._col_width : 2*self._col_width));
  let total_col_widths = col_widths.reduce((sum, cur) => sum + cur, 0);

  let discord_pairs = this._find_discord_pairs(samp_labels, discord);
  let col_spacing = this._make_col_spacing(S, discord_pairs, col_widths);
  let total_col_spacing = col_spacing.reduce((sum, cur) => sum + cur, 0);

  let legend_x_offset = total_col_widths + this._legend_splotch_spacing + total_col_spacing;
  let legend_y_offset = col_label_height + this._discord_height + this._discord_spacing + 0.5*this._legend_splotch_size;
  let legend_width = this._legend_splotch_size + this._legend_padding + pop_label_width;

  let canvas_width = legend_x_offset + legend_width;
  let canvas_height = Math.max(
    col_label_height + this._label_padding + this._col_height,
    legend_y_offset + K*this._legend_splotch_size,
  );
  let svg = d3.select(container).append('svg:svg')
    .attr('width', canvas_width)
    .attr('height', canvas_height);

  let discord_colour = d3.interpolateViridis;
  this._plot_etas(
    svg,
    eta,
    samp_labels,
    col_widths,
    col_spacing,
    pop_colours,
    col_label_height
  );
  this._plot_discord(
    svg,
    discord_pairs,
    col_label_height,
    col_widths,
    col_spacing,
    discord_colour,
  );
  this._add_pop_legend(
    svg,
    pop_labels,
    pop_colours,
    legend_x_offset,
    legend_y_offset
  );
  this._make_discord_legend(
    svg,
    discord_colour,
    legend_x_offset,
    col_label_height,
  );
}
