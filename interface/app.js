/* Radar Seazone — interface (DOM + roteamento hash). Somente exibe os outputs do pipeline. */
(function () {
  'use strict';

  /* ---------- estado ---------- */
  var state = null;
  var fracasso = null;

  /* ---------- helpers ---------- */
  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function labelBairro(b) { return esc(b); }
  function quartoTok(key) {
    var k = String(key || '').trim();
    var partes = k.split('|');
    return partes.length === 3 ? partes[2] : null;
  }
  function labelTipo(tipo, key) {
    var q = quartoTok(key);
    if (q === null) q = String(key).trim();
    var ql = q === '(todos quartos)' || q === '(todos os quartos)' ? 'todos os quartos' : (q === '4+' ? '4+' : (q + ' quarto' + (q === '1' ? '' : 's')));
    var tl = tipo === 'apartamento' ? 'Apartamento' : (tipo === 'casa' ? 'Casa' : (tipo === 'outros' ? 'Outros' : esc(tipo)));
    return esc(tl) + ' · ' + esc(ql);
  }
  function pillStatus(status) {
    if (status === 'prioritaria') return '<span class="pill prioritaria">Prioritário</span>';
    if (status === 'nao_prioritaria') return '<span class="pill nao_prioritaria">Avaliado · não priorizado</span>';
    if (status === 'inconclusiva') return '<span class="pill inconclusiva">Evidência insuficiente</span>';
    return '<span class="pill neutra">' + esc(status) + '</span>';
  }
  function pillNivel(nivel) {
    var map = {
      'bairro×tipo×quartos': 'Nível: bairro × tipo × quartos',
      'bairro×tipo': 'Nível de fallback: bairro × tipo',
      'bairro': 'Nível de fallback: bairro',
      'n/a': 'Nível: n/a'
    };
    return '<span class="pill neutra">' + esc(map[nivel] || nivel) + '</span>';
  }

  function segByKey(key) {
    if (!state) return null;
    return state.seg.find(function (s) { return s.key === key; }) || null;
  }

  /* posição da barra R dentro do domínio global */
  function rBar(s, mini) {
    var dom = state.dom;
    var span = dom.hi - dom.lo;
    if (!span || s.icLo === null || s.icHi === null) return '';
    var lo = Math.max(0, (s.icLo - dom.lo) / span) * 100;
    var hi = Math.min(100, (s.icHi - dom.lo) / span) * 100;
    var r = Math.min(100, Math.max(0, (s.R - dom.lo) / span)) * 100;
    var minW = mini ? 1.2 : 1.6;
    var width = Math.max(minW, hi - lo);
    var base = 'barra R (IC95)';
    return '<div class="range ' + (mini ? 'mini' : '') + '" role="img" aria-label="' + base + '">' +
      '<div class="band" style="left:' + lo.toFixed(2) + '%;width:' + width.toFixed(2) + '%"></div>' +
      '<div class="dot" style="left:' + r.toFixed(2) + '%"></div></div>' +
      '<div class="range-lab"><span>' + RadarData.fmtR(s.icLo) + '</span><span>' + RadarData.fmtR(s.icHi) + '</span></div>';
  }

  /* ---------- roteamento ---------- */
  function parseHash() {
    var h = (location.hash || '#/mercado').replace(/^#/, '').split('/').filter(function (x) { return x !== ''; });
    return h.map(function (x) {
      try { return decodeURIComponent(x); } catch (e) { return x; }
    });
  }
  function go(hash) {
    if (location.hash === hash) { render(); return; }
    location.hash = hash;
  }
  window.addEventListener('hashchange', function () {
    if (state) render();
    else boot();
  });

  /* ---------- breadcrumb ---------- */
  function crumbs(items) {
    var html = '<ol>';
    items.forEach(function (it, i) {
      if (it.link) html += '<li><a href="' + it.link + '">' + esc(it.label) + '</a></li>';
      else html += '<li class="cur">' + esc(it.label) + '</li>';
    });
    html += '</ol>';
    document.getElementById('crumbs').innerHTML = html;
  }

  /* ---------- views ---------- */
  function viewMercado() {
    var c = state.counts, cf = state.confianca;
    crumbs([{ label: 'Mercado' }]);
    var segLista = state.seg.filter(function (s) { return s.status === 'prioritaria'; })
      .sort(function (a, b) { return (b.R || 0) - (a.R || 0); });

    var motivoTiles = Object.keys(state.motivoCount).sort().map(function (m) {
      return '<span class="pill insuficiente">' + esc(m) + ': ' + state.motivoCount[m] + '</span>';
    }).join(' ');

    return '' +
      '<div class="page-head">' +
      '  <span class="eyebrow">Mercado</span>' +
      '  <h1>Radar de mercado · Itapema (SC)</h1>' +
      '  <p>Leitura comparativa de potencial para a operação de curta temporada, construída a partir dos outputs do pipeline de análise. A jornada: <b>mercado → segmentos prioritários → detalhe → candidatos operacionais → evidências</b>.</p>' +
      '</div>' +

      '<div class="tiles">' +
      '  <div class="tile hero"><div class="k">Segmentos prioritários</div><div class="v">' + c.prioritaria + '</div><div class="d">Aprovados pela cascata S1 (elegíveis, não dominados e que dominam ≥ 1 segmento).</div></div>' +
      '  <div class="tile"><div class="k">Candidatos operacionais</div><div class="v">' + c.candidatos + '</div><div class="d">Anúncios nos segmentos prioritários com preço e ≥ 20 datas observadas.</div></div>' +
      '  <div class="tile"><div class="k">Segmentos avaliados</div><div class="v">' + state.seg.length + '</div><div class="d">Com evidência suficiente para estimar R e comparar (' + c.nao_prioritaria + ' não priorizados).</div></div>' +
      '  <div class="tile"><div class="k">Evidência insuficiente</div><div class="v">' + c.inconclusivas + '</div><div class="d">Segmentos inconclusivos que não entram na recomendação.</div></div>' +
      '</div>' +

      '<div class="flow" style="margin-top:22px">' +

      '  <div class="card">' +
      '    <div class="section-title">Confiança da leitura</div>' +
      '    <div class="legend">' +
      '      <span><i style="background:var(--coral)"></i>Janela observada: <b>' + esc(cf.periodo || 'jan–abr 2025') + '</b></span>' +
      '      <span><i style="background:var(--coral)"></i>Sem ocupação em dados</span>' +
      '      <span><i style="background:var(--coral)"></i>Sem receita realizada</span>' +
      '      <span><i style="background:var(--coral)"></i>Sem ROI / yield</span>' +
      '      <span><i style="background:var(--coral)"></i>Sem matching individual Airbnb × VivaReal</span>' +
      '    </div>' +
      '    <div class="legend" style="margin-top:9px">' +
      '      <span>Preço anunciado ≠ transação · amostra do Price cobre ' + (cf.n_ai_global && cf.total_airbnb ? Math.round(cf.n_ai_global / cf.total_airbnb * 100) + '% dos anúncios (concentrada em ativos/profissionais)' : 'parcialmente') + '.</span>' +
      '    </div>' +
      '  </div>' +

      '  <div class="card">' +
      '    <div class="section-title">Começar a jornada</div>' +
      '    <p style="color:var(--suave);font-size:14.5px;margin-bottom:14px">Os <b>segmentos prioritários</b> são o ponto de entrada. Nenhum número é recalculado aqui: tudo vem direto dos outputs do pipeline.</p>' +
      '    <div class="linklist">' +
      segLista.map(function (s) {
        return '<a href="#/segmento/' + encodeURIComponent(s.key) + '">' +
          '<span><b style="color:var(--navy)">' + labelBairro(s.bairro) + '</b> · ' + labelTipo(s.tipo, s.key) + '</span>' +
          '<span class="cnt">R ' + RadarData.fmtR(s.R) + ' · ' + (s.n_alvos != null ? s.n_alvos : 0) + ' candidatos →</span></a>';
      }).join('') +
      '    </div>' +
      '    <div style="margin-top:14px"><a class="btn" href="#/segmentos">Ver todos os segmentos avaliados</a></div>' +
      '  </div>' +

      '  <div class="card">' +
      '    <div class="section-title">Quatro conceitos, quatro papéis</div>' +
      '    <div class="gloss">' +
      '      <div class="g"><span class="tag atr">Atratividade comparativa</span><div class="name">R (indicador comparativo)</div><p>Mediana da diária anunciada (Airbnb) ÷ mediana do preço de venda anunciado (VivaReal) <b>no mesmo segmento</b>. É índice comparativo de potencial — não é ROI, yield ou retorno.</p></div>' +
      '      <div class="g"><span class="tag ev">Evidência</span><div class="name">Dados que sustentam a leitura</div><p>Observações, cobertura do Price, intervalos de confiança e dominância estatística com FDR. A evidência qualifica <b>o que pode ser afirmado</b>.</p></div>' +
      '      <div class="g"><span class="tag el">Elegibilidade</span><div class="name">Critérios mínimos</div><p>n_ai ≥ 5, n_vi com preço ≥ 5 e meia-largura do IC95(R) ≤ 0,60. Sem isso o segmento é <b>inconclusivo</b> e não vira recomendação.</p></div>' +
      '      <div class="g"><span class="tag cand">Candidato operacional</span><div class="name">Anúncio para análise</div><p>Imóvel com sinais operacionais descritivos no segmento prioritário. <b>Não é recomendação de compra</b>: não há preço de venda individual atribuído.</p></div>' +
      '    </div>' +
      '  </div>' +

      '  <div class="card">' +
      '    <div class="section-title">Segmentos inconclusivos · evidência insuficiente</div>' +
      '    <p style="color:var(--suave);font-size:14px;margin-bottom:12px">' + c.inconclusivas + ' segmentos não atingiram a elegibilidade e permanecem visíveis abaixo — apresentados como <b>evidência insuficiente</b>, nunca como recomendação. O motivo registrado pelo pipeline é o critério de exibição.</p>' +
      '    <div style="margin-bottom:12px">' + (motivoTiles || '<span class="pill neutra">—</span>') + '</div>' +
      '    <div class="table-scroll" style="max-height:320px"><table>' +
      '      <thead><tr><th>Bairro</th><th>Tipo</th><th>Quartos</th><th>Motivo</th><th>n_ai</th><th>n_vi (preço)</th><th>Cobertura</th></tr></thead><tbody>' +
      state.inconcl.map(function (r) {
        return '<tr><td class="capitalize">' + labelBairro(r.bairro) + '</td><td>' + esc(r.tipo) + '</td><td>' + esc(r.quartos) + '</td>' +
          '<td><span class="pill insuficiente">' + esc(r.motivo) + '</span></td>' +
          '<td class="mono">' + (r.n_ai == null ? '—' : r.n_ai) + '</td>' +
          '<td class="mono">' + (r.n_vi_sale == null ? '—' : r.n_vi_sale) + '</td>' +
          '<td class="mono">' + RadarData.fmtCov(r.cobertura) + '</td></tr>';
      }).join('') +
      '      </tbody></table></div>' +
      '  </div>' +
      '</div>';
  }

  function viewSegmentos() {
    crumbs([{ label: 'Mercado', link: '#/mercado' }, { label: 'Segmentos avaliados' }]);
    var lista = state.seg.slice().sort(function (a, b) {
      if (a.status !== b.status) return a.status === 'prioritaria' ? -1 : 1;
      return (b.R || 0) - (a.R || 0);
    });

    return '' +
      '<a class="backlink" href="#/mercado">← Mercado</a>' +
      '<div class="page-head">' +
      '  <span class="eyebrow">S1 · Priorização de segmentos</span>' +
      '  <h1>Segmentos avaliados</h1>' +
      '  <p>' + state.counts.prioritaria + ' prioritários e ' + state.counts.nao_prioritaria + ' avaliados sem priorização, ordenados pelo próprio indicador R do segmento. Clique para ver detalhe, evidência e candidatos.</p>' +
      '</div>' +
      '<div class="legend" style="margin-bottom:16px">' +
      '  <span><i style="background:var(--azul)"></i>R — indicador comparativo (mediana diária ÷ mediana preço de venda, mesmo segmento)</span>' +
      '  <span><i style="background:#C9D6EE"></i>Banda = IC95(R)</span>' +
      '  <span><i style="background:var(--ok)"></i>Prioritário</span>' +
      '  <span><i style="background:#5A6B8A"></i>Não priorizado</span>' +
      '</div>' +
      '<div class="seg-list">' +
      lista.map(function (s) {
        var dom = s.evidencia && s.evidencia.dominancia ? s.evidencia.dominancia : null;
        var domTxt = dom && dom.n != null
          ? 'domina ' + dom.n + ' segmento' + (dom.n === 1 ? '' : 's') + ' (FDR)'
          : (s.status === 'prioritaria' ? 'sem lista de dominância registrada' : 'sem dominância estatística');
        return '<a class="seg-row" href="#/segmento/' + encodeURIComponent(s.key) + '">' +
          '<div class="left">' +
          '  <div class="bairro">' + labelBairro(s.bairro) + '</div>' +
          '  <div class="tipo">' + labelTipo(s.tipo, s.key) + '</div>' +
          '  <div class="desc">' +
          '    <span>' + pillNivel(s.nivel) + '</span>' +
          '    <span>' + pillStatus(s.status) + '</span>' +
          '  </div>' +
          '  <div class="desc" style="margin-top:8px">' +
          '    <span>n_ai ' + (s.n_ai == null ? '—' : s.n_ai) + '</span>' +
          '    <span>cobertura ' + RadarData.fmtCov(s.cobertura) + '</span>' +
          '    <span>' + esc(domTxt) + '</span>' +
          '  </div>' +
          '</div>' +
          '<div class="right">' +
          '  <div class="rval">' + RadarData.fmtR(s.R) + '<small>R</small></div>' +
          rBar(s, true) +
          '</div>' +
          '</a>';
      }).join('') +
      '</div>';
  }

  function detailChips(s) {
    return '<div class="badge-row">' + pillStatus(s.status) + pillNivel(s.nivel) + '</div>';
  }

  function buildDetail(s) {
    crumbs([
      { label: 'Mercado', link: '#/mercado' },
      { label: 'Segmentos avaliados', link: '#/segmentos' },
      { label: labelBairro(s.bairro) + ' · ' + labelTipo(s.tipo, s.key) }
    ]);
    var ev = s.evidencia;
    var limite = ev ? (ev.lines.filter(function (l) { return l.indexOf('Limitações:') === 0; }).join(' ')) : null;

    var domTxt = ev && ev.dominancia ? ev.dominancia.linha.replace(/^Dominância contra outros segmentos/i, 'Comparação contra outros segmentos') : 'Não há registro de dominância para este segmento.';

    /* checklist de elegibilidade contra os critérios fixos da metodologia */
    var checkok = function (ok) { return ok ? ' style="color:var(--ok);font-weight:700"' : ' style="color:#B23A33;font-weight:700"'; };
    var elCheck =
      '<div class="ev-block">' +
      '  <div class="ev-line"><span class="k">Critério fixo</span>' + esc('n_ai (Airbnb com preço) ≥ 5') + ' → ' + '<b' + checkok(s.n_ai >= 5) + '>' + (s.n_ai == null ? '—' : s.n_ai) + '</b></div>' +
      '  <div class="ev-line"><span class="k">Critério fixo</span>' + esc('n_vi com preço de venda ≥ 5') + ' → ' + '<b' + checkok(s.n_vi_sale >= 5) + '>' + (s.n_vi_sale == null ? '—' : s.n_vi_sale) + '</b></div>' +
      '  <div class="ev-line"><span class="k">Critério fixo</span>' + esc('meia-largura IC95(R) ≤ 0,60') + ' → ' + '<b' + checkok(s.half != null && s.half <= 0.60) + '>' + (s.half == null ? '—' : RadarData.fmtHalf(s.half)) + '</b></div>' +
      '</div>';

    var razao;
    if (s.status === 'prioritaria') {
      razao = '<div class="notice ok"><span class="ic">✓</span><div><b>Priorizado pela cascata S1.</b> Elegível e estatisticamente não dominado, com dominância comprovada sobre ao menos um outro segmento (Δ, FDR 5%, Δ_min = 25%).</div></div>';
    } else {
      razao = '<div class="notice info"><span class="ic">i</span><div><b>Avaliado, mas não priorizado.</b> O segmento é elegível, porém não atende à condição de dominância da cascata S1 — segue exibido com transparência, sem dominar nenhum concorrente.</div></div>';
    }

    return '' +
      '<a class="backlink" href="#/segmentos">← Todos os segmentos</a>' +
      '<div class="page-head">' +
      '  <span class="eyebrow">Detalhe do segmento</span>' +
      '  <h1 class="capitalize">' + labelBairro(s.bairro) + ' — ' + labelTipo(s.tipo, s.key) + '</h1>' +
      '  <p style="margin-top:12px">' + detailChips(s) + '</p>' +
      '</div>' +

      '<div class="tiles" style="margin-bottom:18px">' +
      '  <div class="tile hero"><div class="k">R · indicador comparativo</div><div class="v">' + RadarData.fmtR(s.R) + '</div><div class="d">Mediana diária anunciada ÷ mediana preço de venda anunciado, mesmo segmento.</div></div>' +
      '  <div class="tile"><div class="k">IC95(R)</div><div class="v"><small>[' + RadarData.fmtR(s.icLo) + ', ' + RadarData.fmtR(s.icHi) + ']</small></div><div class="d">Bootstrap por cluster (anúncio), amostras Airbnb/VivaReal independentes.</div></div>' +
      '  <div class="tile"><div class="k">Observações utilizadas</div><div class="v">' + (s.n_ai == null ? '—' : s.n_ai) + '<small> / ' + (s.n_vi_sale == null ? '—' : s.n_vi_sale) + '</small></div><div class="d">n_ai (Airbnb com preço) / n_vi com preço de venda observado.</div></div>' +
      '  <div class="tile"><div class="k">Cobertura do Price</div><div class="v">' + RadarData.fmtCov(s.cobertura) + '</div><div class="d">Representatividade da amostra de preços no segmento.</div></div>' +
      '  <div class="tile"><div class="k">Precisão</div><div class="v">' + (s.half == null ? '—' : RadarData.fmtHalf(s.half)) + '</div><div class="d">Meia-largura do IC95(R) — quanto menor, mais precisa a estimativa.</div></div>' +
      '</div>' +

      '<div class="card" style="margin-bottom:18px">' +
      '  <div class="section-title">R do segmento no contexto geral</div>' +
      rBar(s, false) +
      '  <p style="font-size:12.5px;color:var(--fosco);margin-top:12px">Banda = IC95(R). Escala única para todos os segmentos avaliados; posição relativa de ' + esc(s.bairro) + '.</p>' +
      '</div>' +

      '<div class="split">' +
      '  <div class="flow">' +
      '    <div class="card">' +
      '      <div class="section-title">Por que este segmento foi priorizado</div>' +
      razao +
      '      <div class="ev-block" style="margin-top:13px">' +
      '        <div class="ev-line"><span class="k">Comparação relevante (verbatim do pipeline)</span><div style="margin-top:2px">' + esc(domTxt) + '</div></div>' +
      '      </div>' +
      '    </div>' +

      '    <div class="card">' +
      '      <div class="section-title">Evidência completa</div>' +
      '      <div class="ev-block">' +
      (ev ? ev.lines.map(function (l) {
        var cls = l.indexOf('Limitações:') === 0 ? ' style="border-bottom:0;margin-top:4px"' : '';
        var k = '';
        if (l.indexOf('Segmento:') === 0) k = 'Identificação';
        else if (l.indexOf('Status:') === 0) k = 'Status';
        else if (l.indexOf('R =') === 0) k = 'Indicador';
        else if (l.indexOf('IC95') === 0) k = 'Incerteza';
        else if (l.indexOf('Observações') === 0) k = 'Volume';
        else if (l.indexOf('Cobertura') === 0) k = 'Cobertura';
        else if (l.indexOf('Dominância') === 0) k = 'Comparação';
        else if (l.indexOf('Limitações:') === 0) k = 'Limitações';
        return '<div class="ev-line"' + cls + '><span class="k">' + esc(k) + '</span><div>' + esc(l) + '</div></div>';
      }).join('') : '<div class="ev-line">Sem registro de evidência no output.</div>') +
      '      </div>' +
      '    </div>' +

      '    <div class="card">' +
      '      <div class="section-title">Limitações que enquadram a leitura</div>' +
      '      <ul style="margin:0 0 0 18px;font-size:13.5px;color:var(--suave);line-height:1.7">' +
      '        <li>Preço anunciado (Airbnb e VivaReal), <b>não</b> é receita, ocupação ou transação fechada.</li>' +
      '        <li>Janela observada jan–abr/2025 (alta temporada parcial) — não generaliza o ano.</li>' +
      '        <li>Junção Airbnb × VivaReal feita <b>agregada por segmento</b>; sem correspondência individual imóvel a imóvel.</li>' +
      (limite ? '<li>' + esc(limite.replace(/^Limitações:\s*/i, '')) + '</li>' : '') +
      '      </ul>' +
      '    </div>' +
      '  </div>' +

      '  <div class="flow">' +
      '    <div class="card">' +
      '      <div class="section-title">Elegibilidade</div>' +
      '      <p style="font-size:13.5px;color:var(--suave);margin-bottom:12px">Critérios fixos da metodologia (congelada). Este segmento está na base avaliada porque os cumpre.</p>' +
      elCheck +
      '    </div>' +

      '    <div class="card">' +
      '      <div class="section-title">Próximo passo</div>' +
      '      <p style="font-size:13.5px;color:var(--suave);margin-bottom:13px">' + (s.n_alvos != null ? s.n_alvos : 0) + ' candidatos operacionais mapeados neste segmento.</p>' +
      '      <a class="btn" href="#/segmento/' + encodeURIComponent(s.key) + '/candidatos">Ver candidatos operacionais</a>' +
      '      <div class="notice warn" style="margin-top:14px"><span class="ic">!</span><div><b>Não é recomendação de compra.</b> R compara segmentos; nenhum preço de venda individual é atribuído a um anúncio Airbnb.</div></div>' +
      '    </div>' +

      (s.status === 'prioritaria' ? '' : '<div class="card"><div class="section-title">Na prática</div><p style="font-size:13.5px;color:var(--suave)">Apesar de elegível, este segmento não obteve dominância estatística. Recomenda-se tratá-lo com cautela em originação.</p></div>') +
      '  </div>' +
      '</div>';
  }

  function viewDetail(key) {
    var s = segByKey(key);
    if (!s) {
      crumbs([{ label: 'Mercado', link: '#/mercado' }, { label: 'Segmentos avaliados', link: '#/segmentos' }, { label: 'Segmento' }]);
      return '<div class="error-state">Segmento não encontrado. <a href="#/segmentos" style="color:inherit">Voltar para a lista</a>.</div>';
    }
    return buildDetail(s);
  }

  function candCard(c, s) {
    var badges = '';
    if (c.superhost) badges += '<span class="tagmini on">Superhost</span>';
    if (c.profissional) badges += '<span class="tagmini on">Profissional</span>';
    if (c.instant) badges += '<span class="tagmini on">Reserva instantânea</span>';
    if (c.guest_favorite) badges += '<span class="tagmini warn">Favorito de hóspedes</span>';
    return '' +
      '<div class="cand">' +
      '  <div class="top">' +
      '    <div><div class="id">#' + esc(c.id) + '</div><div style="font-size:12px;color:var(--suave);margin-top:3px">' + esc(c.quartos === '(todos quartos)' ? 'todos os quartos' : c.quartos + ' quarto' + (c.quartos === '1' ? '' : 's')) + ' · ' + (c.n_datas != null ? c.n_datas : '—') + ' datas com preço</div></div>' +
      '    <div class="diaria"><small>Diária mediana</small>' + RadarData.fmtMoney(c.diaria) + '</div>' +
      '  </div>' +
      '  <div class="body">' +
      '    <div class="linha"><span class="lab">Avaliação</span><span class="val"><span class="stars">★ ' + RadarData.fmtRating(c.rating) + '</span></span></div>' +
      '    <div class="linha"><span class="lab">Reviews</span><span class="val">' + (c.reviews == null ? '—' : c.reviews) + ' · ' + (c.reviews_ano == null ? '—' : RadarData.fmtSmall(c.reviews_ano)) + ' /ano</span></div>' +
      '    <div class="linha"><span class="lab">Capacidade</span><span class="val">' + (c.hóspedes == null ? '—' : c.hóspedes) + ' hóspedes · ' + (c.camas == null ? '—' : c.camas) + ' camas</span></div>' +
      '    <div class="linha"><span class="lab">Taxa de limpeza</span><span class="val">' + RadarData.fmtMoney(c.limpeza) + '</span></div>' +
      '    <div class="linha"><span class="lab">Operação</span><span class="val">' + (c.maturidade == null ? '—' : RadarData.fmtSmall(c.maturidade) + ' anos') + ' de anúncio</span></div>' +
      '    <div class="badges">' + badges + '</div>' +
      '  </div>' +
      '</div>';
  }

  function viewCandidatos(key) {
    var s = segByKey(key);
    if (!s) return viewDetail(key);
    var lista = (state.candBySeg[key] || []).slice();
    var ev = s.evidencia;
    var domN = ev && ev.dominancia && ev.dominancia.n != null ? ev.dominancia.n : null;

    crumbs([
      { label: 'Mercado', link: '#/mercado' },
      { label: 'Segmentos avaliados', link: '#/segmentos' },
      { label: labelBairro(s.bairro) + ' · ' + labelTipo(s.tipo, s.key), link: '#/segmento/' + encodeURIComponent(key) },
      { label: 'Candidatos operacionais' }
    ]);

    var sort = new URLSearchParams(location.hash.split('?')[1] || '').get('ordem') || 'diaria-desc';
    var q = encodeURIComponent((new URLSearchParams(location.hash.split('?')[1] || '').get('q') || '').toLowerCase());

    if (sort === 'diaria-desc') lista.sort(function (a, b) { return (b.diaria || 0) - (a.diaria || 0); });
    else if (sort === 'diaria-asc') lista.sort(function (a, b) { return (a.diaria || 0) - (b.diaria || 0); });
    else if (sort === 'reviews') lista.sort(function (a, b) { return (b.reviews || 0) - (a.reviews || 0); });
    else if (sort === 'rating') lista.sort(function (a, b) { return (b.rating || 0) - (a.rating || 0); });
    else if (sort === 'datas') lista.sort(function (a, b) { return (b.n_datas || 0) - (a.n_datas || 0); });

    if (q) lista = lista.filter(function (c) { return c.id.indexOf(q) > -1; });

    return '' +
      '<a class="backlink" href="#/segmento/' + encodeURIComponent(key) + '">← Voltar ao detalhe do segmento</a>' +
      '<div class="page-head">' +
      '  <span class="eyebrow">S2 · Candidatos operacionais</span>' +
      '  <h1 class="capitalize">Candidatos operacionais — ' + labelBairro(s.bairro) + ' · ' + labelTipo(s.tipo, s.key) + '</h1>' +
      '  <p>' + lista.length + ' anúncios Airbnb com sinais operacionais descritivos. As características abaixo são <b>descritivas</b> — nunca interpretadas como upside ou recomendação de compra.</p>' +
      '</div>' +

      '<div class="tiles" style="margin-bottom:18px">' +
      '  <div class="tile hero"><div class="k">Filtro do pipeline</div><div class="v">' + lista.length + '</div><div class="d">Anúncios do segmento com preço disponível e n_datas ≥ 20 (critério operacional conservador).</div></div>' +
      '  <div class="tile"><div class="k">R do segmento</div><div class="v">' + RadarData.fmtR(s.R) + '</div><div class="d">IC95 [' + RadarData.fmtR(s.icLo) + ', ' + RadarData.fmtR(s.icHi) + '] · incide sobre o segmento, não sobre o imóvel.</div></div>' +
      '  <div class="tile"><div class="k">Cobertura do Price</div><div class="v">' + RadarData.fmtCov(s.cobertura) + '</div><div class="d">n_ai = ' + (s.n_ai == null ? '—' : s.n_ai) + ' · amostragem seletiva do Price.</div></div>' +
      (domN != null ? '<div class="tile"><div class="k">Dominância (FDR)</div><div class="v">' + domN + '</div><div class="d">Segmentos estatisticamente dominados pelo segmento.</div></div>' : '') +
      '</div>' +

      '<div class="toolbar">' +
      '  <label for="ordem">Ordenar por</label>' +
      '  <select id="ordem">' +
      options(sort, [['diaria-desc', 'Diária mediana (maior primeiro)'], ['diaria-asc', 'Diária mediana (menor primeiro)'], ['reviews', 'Nº de reviews'], ['rating', 'Avaliação'], ['datas', 'Nº de datas com preço']]) +
      '  </select>' +
      '  <label for="q" style="margin-left:8px">Filtrar por ID</label>' +
      '  <input id="q" type="search" placeholder="ex.: 8838629" value="' + esc(decodeURIComponent(q)) + '" style="padding:8px 10px;border:1px solid #C9D6EE;border-radius:9px;font-size:13.5px;min-width:180px">' +
      '</div>' +

      (lista.length
        ? '<div class="cand-grid">' + lista.map(function (c) { return candCard(c, s); }).join('') + '</div>'
        : '<div class="card"><p style="color:var(--suave)">Nenhum candidato corresponde aos filtros atuais.</p></div>') +

      '<div class="notice warn" style="margin-top:20px"><span class="ic">!</span><div>' +
      '  <b>Candidato operacional ≠ recomendação de compra.</b> Não há preço de venda individual atribuído a estes anúncios (sem matching Airbnb × VivaReal). Diária é preço anunciado de oferta; tração (reviews, rating, superhost) é sinal descritivo de operação, não projeção de retorno.' +
      '</div></div>' +
      '<div class="notice info" style="margin-top:10px"><span class="ic">i</span><div>' +
      '  <b>Evidência do segmento consultável.</b> A leitura de R e a dominância valem para o segmento agregado. Volte ao <a href="#/segmento/' + encodeURIComponent(key) + '" style="color:var(--azul);font-weight:700">detalhe para conferir a evidência completa</a> e as limitações.' +
      '</div></div>';

    function options(sel, opts) {
      return opts.map(function (o) { return '<option value="' + o[0] + '"' + (sel === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('');
    }
  }

  /* ---------- render ---------- */
  var $app = document.getElementById('app');

  function render() {
    if (fracasso) {
      $app.innerHTML = '<div class="error-state">' +
        '<b>Não foi possível carregar os dados do pipeline.</b><br>' + esc(fracasso.message) +
        '<br>Execute a interface a partir do servidor local: <code>python interface/run.py</code> (ou <code>python -m http.server 8000 --directory .</code>) e abra http://localhost:8000/interface/</div>';
      document.getElementById('crumbs').innerHTML = '';
      return;
    }
    if (!state) {
      $app.innerHTML = '<div class="card" style="text-align:center;padding:60px"><div style="font-weight:800;color:var(--navy)">Carregando dados do pipeline…</div></div>';
      return;
    }
    var h = parseHash();
    var sub = function (idx) { return (h[idx] || '').split('?')[0]; };
    var html;
    if (!h.length || h[0] === 'mercado') html = viewMercado();
    else if (h[0] === 'segmentos') {
      if (h[1]) html = sub(1) === 'candidatos' ? viewCandidatos(h[2]) : viewDetail(h[1]);
      else html = viewSegmentos();
    }
    else if (h[0] === 'segmento') html = sub(2) === 'candidatos' ? viewCandidatos(h[1]) : viewDetail(h[1]);
    else html = viewMercado();
    $app.innerHTML = html;
    bindCandidatosFiltros();
    window.scrollTo(0, 0);
    document.getElementById('app').focus({ preventScroll: true });
  }

  /* vínculo de ordenação e busca na tela de candidatos */
  function parametrosAtuais() {
    var qs = location.hash.split('?')[1] || '';
    var obj = {};
    qs.split('&').forEach(function (p) {
      if (!p) return;
      var kv = p.split('=');
      obj[kv[0]] = decodeURIComponent(kv[1] || '');
    });
    return obj;
  }
  function bindCandidatosFiltros() {
    var sel = document.getElementById('ordem');
    if (sel) {
      sel.addEventListener('change', function () {
        var base = location.hash.split('?')[0];
        var obj = parametrosAtuais();
        obj.ordem = sel.value;
        var qs = Object.keys(obj).map(function (k) { return k + '=' + encodeURIComponent(obj[k]); }).join('&');
        location.hash = base + (qs ? '?' + qs : '');
      });
    }
    var inp = document.getElementById('q');
    if (inp) {
      inp.addEventListener('input', function () {
        var base = location.hash.split('?')[0];
        var obj = parametrosAtuais();
        var v = inp.value.trim().toLowerCase();
        if (v) obj.q = v; else delete obj.q;
        var qs = Object.keys(obj).map(function (k) { return k + '=' + encodeURIComponent(obj[k]); }).join('&');
        var alvo = base + (qs ? '?' + qs : '');
        if (location.hash !== alvo) location.hash = alvo;
      });
    }
  }

  function boot() {
    document.getElementById('crumbs').innerHTML = '';
    $app.innerHTML = '<div class="card" style="text-align:center;padding:60px"><div style="font-weight:800;color:var(--navy)">Carregando dados do pipeline…</div></div>';
    RadarData.loadAll().then(function (st) {
      state = st;
      render();
    }).catch(function (err) {
      fracasso = { message: (err && err.message) ? err.message : String(err) };
      render();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();