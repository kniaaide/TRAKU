// Función para mostrar notificaciones personalizadas
function mostrarNotificacion(mensaje, tipo = 'info') {
    console.log(`[TRAKU NOTIFICACIÓN]: ${mensaje}`);
    // Puedes usar un alert o una librería como SweetAlert
    alert(mensaje);
}

// Lógica para checar tareas próximas (Simulación)
function checarTareasProximas() {
    // Aquí podrías hacer un fetch a tu JSON para ver qué tareas vencen hoy
    console.log("Revisando agenda del estudiante...");
}

// Ejecutar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    checarTareasProximas();
    
    // Si el usuario es estudiante, le recordamos sus deberes
    const badge = document.querySelector('.role-badge');
    if (badge && badge.innerText === 'estudiante') {
        setTimeout(() => {
            mostrarNotificacion("¡Hola! No olvides revisar tu calendario para las tareas de esta semana.");
        }, 2000);
    }
});