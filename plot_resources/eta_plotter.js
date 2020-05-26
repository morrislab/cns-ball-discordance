function EtaPlotter() {
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

EtaPlotter.prototype._transpose = function(mat) {
  var J = mat.length;
  var K = mat[0].length;

  var T = [];
  for(let k = 0; k < K; k++) {
    T.push([]);
    for(let j = 0; j < J; j++) {
      T[k].push(mat[j][k]);
    }
  }

  return T;
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

EtaPlotter.prototype.plot = function(eta, samp_labels, container) {
  var bar_width = 50;
  var bar_height = 600;
  var legend_spacing = 60;
  var font_size = '16px';
  var label_padding = 10;

  var K = eta.length;
  var S = eta[0].length;
  var K_range = Array.from(Array(K).keys());
  var S_range = Array.from(Array(S).keys());
  var eta_cum = this._calc_cum(eta);
//var eta_T = this._transpose(eta);

  let pop_labels =  K_range.map(idx => 'Pop. ' + idx);
  let pop_colours = ColourAssigner.assign_colours(K);
  let row_label_width = this._calc_label_width(pop_labels);
  let col_label_height = this._calc_label_width(samp_labels);

  if(pop_labels.length !== K) {
    throw "Wrong number of pop labels";
  }
  if(samp_labels.length !== S) {
    throw "Wrong number of samp labels";
  }

  var svg = d3.select(container).append('svg:svg')
    .attr('width', S * bar_width)
    .attr('height', col_label_height + label_padding + bar_height);
  var cl = svg.append('svg:g')
    .attr('transform', function(d, i) { return 'translate(' + (0.5 * bar_width) + ',' + (col_label_height - label_padding) + ')'; })
    .selectAll('text')
    .data(samp_labels)
    .join('svg:text')
    .attr('transform', function(d, i) { return 'translate(' + i * bar_width + ',0) rotate(270)'; })
    .attr('x', 0)
    .attr('y', 0)
    .attr('font-size', font_size)
    .attr('font-weight', 'bold')
    .text(function(d, i) { return d; });

  var cols = svg.selectAll('g.col')
    .data(S_range)
    .join('svg:g')
    .attr('class', 'col')
    .attr('transform', function(d, i) { return 'translate(' + i*bar_width + ',' + col_label_height + ')'; });
  /*rows.append('text')
    .attr('x', -label_padding)
    .attr('y', 0.5 * cell_size)
    .attr('dominant-baseline', 'middle')
    .attr('text-anchor', 'end')
    .attr('font-size', font_size)
    .attr('font-weight', 'bold')
    .text(function(d, i) { return pop_labels[i]; });*/

  var rect = cols.selectAll('rect')
    .data(function(sidx) { return K_range.map(function(k) { return {k: k, s: sidx}; }); })
    .join('svg:rect')
    .attr('width', bar_width)
    .attr('height', function(d) { return eta[d.k][d.s] * bar_height; })
    .attr('x', 0)
    .attr('y', function(d, i) { return eta_cum[d.k][d.s] * bar_height; })
    .attr('fill-opacity', function(d) { return 1.0; })
    .attr('fill', function(d, i) { return pop_colours[i]; });
}
