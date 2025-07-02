import matplotlib.pyplot as plt
import contextily as ctx

MAP_TILES_THEMES = {
    "stadiaDark": ctx.providers.Stadia.AlidadeSmoothDark,
    "stadiaLight": ctx.providers.Stadia.AlidadeSmooth,
    "cartoDBPositron": ctx.providers.CartoDB.Positron,
    "cartoDBVoyager": ctx.providers.CartoDB.Voyager,
    "cartoDBDarkMatter": ctx.providers.CartoDB.DarkMatter,
}
RJ_MAP_LIMIT_COORDINATES = [
    [-43.7955, -23.0827],
    [-43.0990, -22.7469]
]

def generate_map(markingPoints: list):
    'Recebe uma lista de pontos e de gera os frames com os pontos marcados'
    x_min, y_min = RJ_MAP_LIMIT_COORDINATES[0]
    x_max, y_max = RJ_MAP_LIMIT_COORDINATES[1]
    largura = abs(x_max - x_min)
    altura = abs(y_max - y_min)
    proporcao = largura / altura
    altura_fig = 5
    largura_fig = proporcao * altura_fig

    figure, eixos = plt.subplots(figsize=(largura_fig, altura_fig))

    eixos.axis('off')
    eixos.set_xlim(RJ_MAP_LIMIT_COORDINATES[0][0], RJ_MAP_LIMIT_COORDINATES[1][0])
    eixos.set_ylim(RJ_MAP_LIMIT_COORDINATES[0][1], RJ_MAP_LIMIT_COORDINATES[1][1])

    ctx.add_basemap(eixos, crs="EPSG:4326", source=MAP_TILES_THEMES["cartoDBPositron"], zoom=16)
    plt.savefig('mapa_rj.png', bbox_inches='tight', pad_inches=0, dpi=200)
    plt.close(figure)

generate_map()