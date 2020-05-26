function EtaPlotter() {
  this._bar_width = 50;
  this._bar_height = 600;
  this._legend_spacing = 60;
  this._font_size = '16px';
  this._label_padding = 10;
}

EtaPlotter.prototype._calc_label_width = function(labels) {
  var max_length = 0;
  var char_width = 15;
  for(let label of labels) {
    if(label.length > max_length) {
      max_length = label.length;
    }
  }
  return char_width * max_length;
}

EtaPlotter.prototype._calc_cum = function(mat) {
  var K = mat.length;
  var S = mat[0].length;
  var S_range = Array.from(Array(S).keys());

  var cum = [S_range.map(d => 0)];
  for(let k = 1; k < K; k++) {
    cum.push(S_range.map(s => cum[k - 1][s] + mat[k - 1][s]));
  }
  return cum;
}

EtaPlotter.prototype._plot_etas = function(svg, eta, samp_labels, col_label_height) {
  let self = this;
  let K = eta.length;
  let S = eta[0].length;
  let K_range = Array.from(Array(K).keys());
  let S_range = Array.from(Array(S).keys());
  let eta_cum = this._calc_cum(eta);

  if(samp_labels.length !== S) {
    throw "Wrong number of samp labels";
  }

  let cl = svg.append('svg:g')
    .attr('transform', function(d, i) { return 'translate(' + (0.5 * self._bar_width) + ',' + (col_label_height - self._label_padding) + ')'; })
    .selectAll('text')
    .data(samp_labels)
    .join('svg:text')
    .attr('transform', function(d, i) { return 'translate(' + i * self._bar_width + ',0) rotate(270)'; })
    .attr('x', 0)
    .attr('y', 0)
    .attr('font-size', this._font_size)
    .attr('font-weight', 'bold')
    .text(function(d, i) { return d; });

  let cols = svg.selectAll('g.col')
    .data(S_range)
    .join('svg:g')
    .attr('class', 'col')
    .attr('transform', function(d, i) { return 'translate(' + i*self._bar_width + ',' + col_label_height + ')'; });

  let pop_colours = ColourAssigner.assign_colours(K);
  cols.selectAll('rect')
    .data(function(sidx) { return K_range.map(function(k) { return {k: k, s: sidx}; }); })
    .join('svg:rect')
    .attr('width', self._bar_width)
    .attr('height', function(d) { return eta[d.k][d.s] * self._bar_height; })
    .attr('x', 0)
    .attr('y', function(d, i) { return eta_cum[d.k][d.s] * self._bar_height; })
    .attr('fill-opacity', function(d) { return 1.0; })
    .attr('fill', function(d, i) { return pop_colours[i]; });
}

EtaPlotter.prototype._add_pop_legend = function(svg, K, col_label_height) {
  let K_range = Array.from(Array(K).keys());
  let pop_labels =  K_range.map(idx => 'Pop. ' + idx);
  if(pop_labels.length !== K) {
    throw "Wrong number of pop labels";
  }
}

EtaPlotter.prototype.plot = function(eta, samp_labels, container) {
  let K = eta.length;
  let S = eta[0].length;
  let col_label_height = this._calc_label_width(samp_labels);

  let svg = d3.select(container).append('svg:svg')
    .attr('width', S * this._bar_width)
    .attr('height', col_label_height + this._label_padding + this._bar_height);

  this._plot_etas(svg, eta, samp_labels, col_label_height);
  this._add_pop_legend(svg, K, col_label_height);
}
