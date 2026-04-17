from datetime import datetime

_SEASONAL_CALENDAR = {
    1: (
        "Janeiro/Fevereiro — Soja em desenvolvimento vegetativo no Cerrado e Sul. "
        "Produtor preocupado com clima e pragas. Milho verão em enchimento de grãos. "
        "Tópicos quentes: manejo de doenças, previsão climática, mercado de soja."
    ),
    2: (
        "Janeiro/Fevereiro — Soja em desenvolvimento vegetativo no Cerrado e Sul. "
        "Produtor preocupado com clima e pragas. Milho verão em enchimento de grãos. "
        "Tópicos quentes: manejo de doenças, previsão climática, mercado de soja."
    ),
    3: (
        "Março/Abril — Colheita de soja no Centro-Oeste. Segunda safra de milho (safrinha) "
        "em desenvolvimento vegetativo no MT e MS. Produtor tomando decisões de venda e "
        "planejando próxima safra. Tópicos quentes: preço da soja, comercialização, custo de produção, "
        "análise de solo para próxima safra."
    ),
    4: (
        "Março/Abril — Colheita de soja no Centro-Oeste. Segunda safra de milho (safrinha) "
        "em desenvolvimento vegetativo no MT e MS. Produtor tomando decisões de venda e "
        "planejando próxima safra. Tópicos quentes: preço da soja, comercialização, custo de produção, "
        "análise de solo para próxima safra."
    ),
    5: (
        "Maio/Junho — Segunda safra de milho em colheita no Centro-Oeste. Entressafra da soja. "
        "Período de planejamento e compra de insumos para a próxima safra. Café em colheita "
        "(arábica no Sul de MG). Tópicos quentes: planejamento financeiro, insumos, crédito rural, "
        "retenção de soja, preço do milho."
    ),
    6: (
        "Maio/Junho — Segunda safra de milho em colheita no Centro-Oeste. Entressafra da soja. "
        "Período de planejamento e compra de insumos para a próxima safra. Café em colheita "
        "(arábica no Sul de MG). Tópicos quentes: planejamento financeiro, insumos, crédito rural, "
        "retenção de soja, preço do milho."
    ),
    7: (
        "Julho/Agosto — Mercado de insumos aquecido. Produtor definindo fornecedores e fechando "
        "contratos de compra de sementes e fertilizantes para a safra de soja. Regiões mais cedo "
        "já preparam solo. Tópicos quentes: negociação de insumos, análise de solo, escolha de "
        "variedades, planejamento da safra 2026/27."
    ),
    8: (
        "Julho/Agosto — Mercado de insumos aquecido. Produtor definindo fornecedores e fechando "
        "contratos de compra de sementes e fertilizantes para a safra de soja. Regiões mais cedo "
        "já preparam solo. Tópicos quentes: negociação de insumos, análise de solo, escolha de "
        "variedades, planejamento da safra 2026/27."
    ),
    9: (
        "Setembro/Outubro — Plantio de soja começa nas regiões mais precoces (MT, GO). "
        "Cana-de-açúcar em colheita plena no Centro-Sul. Café arábica em colheita final. "
        "Produtor ansioso com janela de plantio e condições climáticas. "
        "Tópicos quentes: época de plantio, tratamento de sementes, população de plantas, "
        "monitoramento de pragas na emergência."
    ),
    10: (
        "Setembro/Outubro — Plantio de soja começa nas regiões mais precoces (MT, GO). "
        "Cana-de-açúcar em colheita plena no Centro-Sul. Café arábica em colheita final. "
        "Produtor ansioso com janela de plantio e condições climáticas. "
        "Tópicos quentes: época de plantio, tratamento de sementes, população de plantas, "
        "monitoramento de pragas na emergência."
    ),
    11: (
        "Novembro/Dezembro — Plantio de soja consolidado em quase todo o Brasil. Milho verão "
        "começando no Sul. Produtor focado no manejo de lavoura (herbicidas, fungicidas). "
        "Tópicos quentes: controle de pragas, manejo de doenças, aplicação de fungicidas "
        "na soja, perspectivas de produção para a safra."
    ),
    12: (
        "Novembro/Dezembro — Plantio de soja consolidado em quase todo o Brasil. Milho verão "
        "começando no Sul. Produtor focado no manejo de lavoura (herbicidas, fungicidas). "
        "Tópicos quentes: controle de pragas, manejo de doenças, aplicação de fungicidas "
        "na soja, perspectivas de produção para a safra."
    ),
}


def get_seasonal_context() -> str:
    """Return the current month's agro seasonal context string."""
    month = datetime.now().month
    return _SEASONAL_CALENDAR[month]
