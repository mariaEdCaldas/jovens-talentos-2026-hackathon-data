/* Radar Seazone — camada de dados (pura, sem DOM).
 * Lê e estrutura os outputs do pipeline de análise.
 * Nenhum cálculo novo: apenas leitura, parsing e formatação dos números já produzidos.
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory();
  else root.RadarData = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var BASE = '..';
  var ARQUIVOS = [
    { nome: 's1_segmentos.csv', rota: 'analise/saida/s1_segmentos.csv' },
    { nome: 's1_inconclusivas.csv', rota: 'analise/saida/s1_inconclusivas.csv' },
    { nome: 's2_candidatos.csv', rota: 'analise/saida/s2_candidatos.csv' },
    { nome: 'evidencias.csv', rota: 'analise/saida/evidencias.csv' },
    { nome: 'recomendacao_segmentos.csv', rota: 'analise/saida/recomendacao_segmentos.csv' },
    { nome: 'pipeline_resultados.json', rota: 'analise/saida/pipeline_resultados.json' }
  ];

  /* ---------- parser CSV (aspas, vírgulas e quebras de linha dentro de campos) ---------- */
  function parseCSV(text) {
    if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
    var rows = [], field = '', row = [], i = 0, inQuotes = false;
    function endField() { row.push(field); field = ''; }
    function endRow() { endField(); if (row.some(function (c) { return c !== ''; })) rows.push(row); row = []; }
    while (i < text.length) {
      var c = text[i];
      if (inQuotes) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i += 2; continue; }
          inQuotes = false; i++; continue;
        }
        if (c === '\r') { i++; continue; }
        field += c; i++; continue;
      }
      if (c === '"') { inQuotes = true; i++; continue; }
      if (c === ',') { endField(); i++; continue; }
      if (c === '\n') { endRow(); i++; continue; }
      if (c === '\r') { i++; continue; }
      field += c; i++;
    }
    if (field !== '' || row.length) endRow();
    if (!rows.length) return [];
    var header = rows[0], out = [];
    for (var r = 1; r < rows.length; r++) {
      var o = {};
      for (var c2 = 0; c2 < header.length; c2++) o[header[c2]] = rows[r][c2];
      out.push(o);
    }
    return out;
  }

  /* ---------- utilidades ---------- */
  function num(v) {
    if (v === null || v === undefined || v === '') return null;
    var n = Number(v);
    return isNaN(n) ? null : n;
  }
  function int(v) { var n = num(v); return n === null ? null : Math.round(n); }
  function canonSeg(s) {
    return String(s).toLowerCase().trim().replace(/\s*\|\s*/g, '|').replace(/\s+/g, ' ');
  }
  function fmtDec(v, casas, ptBR) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    var s = v.toFixed(casas);
    return ptBR ? s.replace('.', ',') : s;
  }
  function fmtR(v) { return fmtDec(v, 5, true); }
  function fmtHalf(v) { return fmtDec(v, 3, true); }
  function fmtCov(v) { return v === null ? '—' : fmtDec(v, 1, true) + '%'; }
  function fmtMoney(v) {
    if (v === null || isNaN(v)) return '—';
    return 'R$ ' + v.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
  }
  function fmtRating(v) { return v === null ? '—' : fmtDec(v, 1, true); }
  function fmtSmall(v, casas) { return fmtDec(v, casas || 1, true); }

  /* ---------- evidências ---------- */
  function parseEvidence(ev) {
    var lines = String(ev.explicacao || '').split('\n').map(function (l) { return l.trim(); }).filter(function (l) { return l !== ''; });
    var o = { chave: ev.chave, segKey: null, status: null, nivel: null, dominancia: null, lines: lines };
    for (var i = 0; i < lines.length; i++) {
      var l = lines[i];
      if (l.indexOf('Segmento:') === 0) {
        var m = l.match(/^Segmento:\s*(.+?)\s*\(nível avaliado:\s*(.+?)\s*\)/i);
        if (m) { o.segKey = canonSeg(m[1]); o.nivel = m[2]; }
      } else if (l.indexOf('Status:') === 0) {
        o.status = l.replace('Status:', '').trim();
      } else if (l.indexOf('Dominância') === 0) {
        var dm = l.match(/domina (\d+) segmento\(s\)?/i);
        o.dominancia = dm ? { n: parseInt(dm[1], 10), linha: l } : { n: null, linha: l };
      }
    }
    return o;
  }

  /* ---------- montagem do estado ---------- */
  function buildFromLoaded(raw) {
    var s1 = raw.s1 || [];
    var inconcl = raw.inconcl || [];
    var cand = raw.cand || [];
    var evRows = raw.ev || [];
    var rec = raw.rec || [];
    var meta = raw.meta || {};

    var evMap = {};
    evRows.forEach(function (ev) {
      var p = parseEvidence(ev);
      if (p.segKey) evMap[p.segKey] = p;
    });

    var recMap = {};
    rec.forEach(function (r) { recMap[canonSeg(r.segmento)] = int(r.n_alvos_candidatos); });

    var seg = s1.map(function (r) {
      var key = canonSeg(r.bairro_tipo_quartos);
      var ev = evMap[key] || null;
      return {
        key: key,
        bairro: r.bairro, tipo: r.tipo, quartos: r.quartos,
        nivel: r.nivel, status: r.status, origin: r.origin,
        R: num(r.R), icLo: num(r.R_ic_lo), icHi: num(r.R_ic_hi), half: num(r.half),
        n_ai: int(r.n_ai), n_vi: int(r.n_vi_total), n_vi_sale: int(r.n_vi_com_sale_price),
        cobertura: num(r.cobertura_price_pct),
        evidencia: ev, n_alvos: recMap[key] !== undefined ? recMap[key] : null
      };
    });

    /* domínio global dos intervalos para as barras R */
    var lo = Infinity, hi = -Infinity;
    seg.forEach(function (s) { if (s.icLo !== null && s.icLo < lo) lo = s.icLo; if (s.icHi !== null && s.icHi > hi) hi = s.icHi; });
    var dom = { lo: lo, hi: hi };

    var candBySeg = {};
    cand.forEach(function (c) {
      var key = canonSeg(c.segmento_prioritario);
      (candBySeg[key] = candBySeg[key] || []).push({
        id: String(c.airbnb_listing_id),
        bairro: c.bairro, tipo: c.tipo, quartos: c.quartos,
        diaria: num(c.diaria_mediana), n_datas: int(c.n_datas),
        reviews: int(c.numero_reviews), reviews_ano: num(c.reviews_ano), rating: num(c.star_rating),
        guest_favorite: c.is_guest_favorite === 'True', superhost: c.is_superhost === 'True',
        profissional: c.is_professional === 'True', instant: c.can_instant_book === 'True',
        limpeza: num(c.cleaning_fee), hóspedes: int(c.n_guests), camas: int(c.n_beds),
        maturidade: num(c.maturidade_anos)
      });
    });

    /* distribuição por motivo nas inconclusivas */
    var motivoCount = {};
    var inconclDet = inconcl.map(function (r) {
      var m = r.motivo || '—';
      motivoCount[m] = (motivoCount[m] || 0) + 1;
      return {
        bairro: r.bairro, tipo: r.tipo, quartos: r.quartos, motivo: m,
        n_ai: int(r.n_ai), n_vi_sale: int(r.n_vi_com_sale_price), cobertura: num(r.cobertura_price_pct)
      };
    });

    var conf = meta.confianca || {};
    var counts = {
      prioritaria: seg.filter(function (s) { return s.status === 'prioritaria'; }).length,
      nao_prioritaria: seg.filter(function (s) { return s.status === 'nao_prioritaria'; }).length,
      inconclusivas: int(meta.n_inconclusivas) != null ? int(meta.n_inconclusivas) : inconclDet.length,
      candidatos: int(meta.n_candidatos_s2) != null ? int(meta.n_candidatos_s2) : cand.length
    };

    return {
      seg: seg,
      inconcl: inconclDet,
      motivoCount: motivoCount,
      cand: cand,
      candBySeg: candBySeg,
      evMap: evMap,
      counts: counts,
      dom: dom,
      confianca: {
        periodo: conf.periodo, n_ai_global: int(conf.n_ai_global), total_airbnb: int(conf.total_airbnb),
        sem_ocupacao: conf.sem_ocupacao, sem_receita: conf.sem_receita, sem_roi: conf.sem_roi,
        sem_matching: conf.sem_matching_individual_airbnb_vivareal, preco_anunciado: conf.preco_anunciado_nao_receita
      },
      meta: meta
    };
  }

  /* ---------- carregamento (browser) ---------- */
  async function loadAll() {
    async function fetchText(rota) {
      var res = await fetch(BASE + '/' + rota);
      if (!res.ok) throw new Error('Falha ao carregar ' + rota + ' (HTTP ' + res.status + ')');
      return res.text();
    }
    var raw = {};
    await Promise.all(ARQUIVOS.map(function (f) {
      return fetchText(f.rota).then(function (t) {
        if (f.nome.indexOf('.json') > -1) raw[f.nome] = JSON.parse(t);
        else raw[f.nome] = parseCSV(t);
      });
    }));
    return buildFromLoaded({
      s1: raw['s1_segmentos.csv'], inconcl: raw['s1_inconclusivas.csv'], cand: raw['s2_candidatos.csv'],
      ev: raw['evidencias.csv'], rec: raw['recomendacao_segmentos.csv'], meta: raw['pipeline_resultados.json']
    });
  }

  return {
    BASE: BASE,
    parseCSV: parseCSV,
    canonSeg: canonSeg,
    num: num, int: int,
    fmtR: fmtR, fmtHalf: fmtHalf, fmtCov: fmtCov, fmtMoney: fmtMoney, fmtRating: fmtRating, fmtSmall: fmtSmall,
    parseEvidence: parseEvidence,
    buildFromLoaded: buildFromLoaded,
    loadAll: loadAll,
    ARQUIVOS: ARQUIVOS
  };
});