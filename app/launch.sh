#!/bin/bash
# Arranque de la app de PRODUCCIÓN via systemd --user
# Esto reemplaza el antiguo: screen + reflex run
#
# Uso:
#   ./launch.sh          → arrancar
#   ./launch.sh stop     → parar
#   ./launch.sh restart  → reiniciar
#   ./launch.sh logs     → ver logs en tiempo real
#   ./launch.sh status   → estado del servicio

set -e

SERVICE="reflex-prod"

case "${1:-start}" in
  start)
    echo "Arrancando $SERVICE..."
    systemctl --user daemon-reload
    systemctl --user start "$SERVICE"
    systemctl --user status "$SERVICE" --no-pager
    echo ""
    echo "Logs: journalctl --user -u $SERVICE -f"
    ;;
  stop)
    echo "Parando $SERVICE..."
    systemctl --user stop "$SERVICE"
    ;;
  restart)
    echo "Reiniciando $SERVICE..."
    systemctl --user daemon-reload
    systemctl --user restart "$SERVICE"
    systemctl --user status "$SERVICE" --no-pager
    ;;
  logs)
    journalctl --user -u "$SERVICE" -f
    ;;
  status)
    systemctl --user status "$SERVICE" --no-pager
    ;;
  enable)
    # Activar para que arranque automáticamente si se reinicia el servidor
    systemctl --user enable "$SERVICE"
    echo "$SERVICE habilitado para arranque automático."
    ;;
  *)
    echo "Uso: $0 {start|stop|restart|logs|status|enable}"
    exit 1
    ;;
esac