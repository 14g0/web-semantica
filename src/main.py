import sparql

sparql.generate_heatmap_paradas_geral_folium()
sparql.generate_heatmap_paradas_linha("O0636AAA0A")
sparql.plot_paradas_linha(43)
# sparql.melhor_rota(-22.882405, -43.341696, -22.839038, -43.239646)