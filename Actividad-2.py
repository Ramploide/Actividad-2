

from heapq import heappush, heappop   # librería estándar para colas de prioridad (usada en Dijkstra)

# =======================================================
# 1. CLASE KNOWLEDGEBASE
# =======================================================
class KnowledgeBase:
    def __init__(self):
        # Diccionario que almacena las conexiones
        # Cada clave es una tupla (origen, destino) y su valor son propiedades de la ruta
        self.edges = {}

    def add_edge(self, u, v, mode, time, cost, bidirectional=True):
        """
        Agrega un hecho al sistema de conocimiento:
        connected(u, v, modo, tiempo, costo).
        Si bidirectional=True, se asume que la ruta es de doble sentido.
        """
        self.edges[(u, v)] = {"mode": mode, "time": time, "cost": cost}
        if bidirectional:
            self.edges[(v, u)] = {"mode": mode, "time": time, "cost": cost}

    def neighbors(self, node):
        """
        Devuelve los vecinos de un nodo (estación) junto con sus propiedades.
        Ejemplo: para 'A' retorna [('B', {...}), ('Centro', {...})]
        """
        for (a, b), props in self.edges.items():
            if a == node:
                yield b, props

    # ------------------------
    # 2. Reglas de inferencia
    # ------------------------
    def make_bidirectional(self):
        """
        Regla de simetría:
        Si existe connected(A,B) pero no connected(B,A),
        se agrega automáticamente.
        """
        new_edges = []
        for (u, v), props in list(self.edges.items()):
            if (v, u) not in self.edges:
                new_edges.append((v, u, props["mode"], props["time"], props["cost"]))
        for u, v, m, t, c in new_edges:
            self.add_edge(u, v, m, t, c, bidirectional=False)

    def add_transfers(self, penalty_time=3.0):
        """
        Regla de transferencia:
        Si en una misma estación confluyen distintos modos de transporte,
        se agrega un "camino a pie" entre esas conexiones.
        Esto simula los transbordos entre líneas.
        """
        new_edges = []
        for (a, b), props1 in list(self.edges.items()):
            for (c, d), props2 in list(self.edges.items()):
                # condición: comparten la estación origen, van a destinos distintos
                # y usan modos diferentes
                if a == c and b != d and props1["mode"] != props2["mode"]:
                    if (b, d) not in self.edges:
                        new_edges.append((b, d, "walk", penalty_time, 0.0))
        # se agregan como conexiones bidireccionales
        for u, v, m, t, c in new_edges:
            self.add_edge(u, v, m, t, c, bidirectional=True)

# =======================================================
# 3. ALGORITMO DE BÚSQUEDA: DIJKSTRA
# =======================================================
def dijkstra(kb, start, goal, metric="time", transfer_penalty=2.0):
    """
    Algoritmo de Dijkstra adaptado:
    - Encuentra la ruta más corta (mínimo acumulado).
    - Puede optimizar tiempo o costo (según 'metric').
    - Se penaliza cada vez que cambia el modo de transporte.
    """
    # Cola de prioridad con: (valor acumulado, nodo actual, modo previo, ruta recorrida)
    pq = [(0, start, None, [start])]
    visited = {}

    while pq:
        acc, node, prev_mode, path = heappop(pq)

        # Caso base: si llegamos al destino, retornamos ruta y costo
        if node == goal:
            return path, acc

        key = (node, prev_mode)
        # Si ya se visitó este nodo con un valor menor, se ignora
        if key in visited and visited[key] <= acc:
            continue
        visited[key] = acc

        # Explorar vecinos
        for neigh, props in kb.neighbors(node):
            next_mode = props["mode"]
            base = props[metric]
            # Penalización si cambiamos de modo de transporte
            penalty = transfer_penalty if prev_mode and prev_mode != next_mode else 0
            new_acc = acc + base + penalty
            heappush(pq, (new_acc, neigh, next_mode, path + [neigh]))

    # Si no hay ruta posible
    return None, float("inf")

# =======================================================
# 4. PROGRAMA PRINCIPAL (MENÚ INTERACTIVO)
# =======================================================
if __name__ == "__main__":
    kb = KnowledgeBase()

    # Base inicial de hechos (red de ejemplo)
    kb.add_edge("A", "B", "metro", 4, 1.5)
    kb.add_edge("B", "C", "metro", 3, 1.2)
    kb.add_edge("C", "D", "metro", 5, 1.8)
    kb.add_edge("B", "P1", "bus", 6, 0.9)
    kb.add_edge("P1", "P2", "bus", 8, 1.1)
    kb.add_edge("P2", "D", "bus", 7, 1.0)
    kb.add_edge("A", "Centro", "tram", 10, 1.7)
    kb.add_edge("Centro", "D", "tram", 9, 1.6)

    # Aplicamos las reglas iniciales
    kb.make_bidirectional()
    kb.add_transfers()

    # -----------------------
    # Bucle del menú principal
    # -----------------------
    while True:
        print("\n=== SISTEMA DE RUTAS ===")
        print("1. Añadir nueva ruta")
        print("2. Consultar mejor ruta")
        print("3. Ver estaciones registradas")
        print("4. Salir")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            # Añadir hecho nuevo
            u = input("Estación origen: ").strip()
            v = input("Estación destino: ").strip()
            mode = input("Modo de transporte (metro/bus/tram): ").strip().lower()
            time = float(input("Tiempo estimado: "))
            cost = float(input("Costo estimado: "))

            kb.add_edge(u, v, mode, time, cost, bidirectional=True)
            kb.make_bidirectional()
            kb.add_transfers()
            print("✅ Ruta añadida correctamente.")

        elif opcion == "2":
            # Mostrar lista de estaciones
            estaciones = sorted(set([u for u, _ in kb.edges.keys()] + [v for _, v in kb.edges.keys()]))
            print("📍 Estaciones disponibles:", ", ".join(estaciones))

            origen = input("Ingrese la estación de origen: ").strip()
            destino = input("Ingrese la estación de destino: ").strip()
            metric = input("¿Optimizar por 'time' o 'cost'?: ").strip().lower()

            if origen not in estaciones or destino not in estaciones:
                print("❌ Estación inválida.")
            elif metric not in ("time", "cost"):
                print("❌ Métrica inválida.")
            else:
                ruta, total = dijkstra(kb, origen, destino, metric=metric)
                if ruta:
                    print(f"\n✅ Ruta óptima {origen} → {destino} optimizando {metric}:")
                    print("  -> ".join(ruta))
                    print(f"Total ({metric} + penalizaciones): {total:.2f}")
                else:
                    print("❌ No existe ruta disponible.")

        elif opcion == "3":
            # Ver estaciones registradas
            estaciones = sorted(set([u for u, _ in kb.edges.keys()] + [v for _, v in kb.edges.keys()]))
            print("📍 Estaciones registradas:", ", ".join(estaciones))

        elif opcion == "4":
            print("👋 Saliendo del sistema...")
            break

        else:
            print("❌ Opción inválida. Intente de nuevo.")
