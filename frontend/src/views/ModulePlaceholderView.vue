<template>
  <section class="card">
    <h1>{{ $route.meta.title }}</h1>
    <p>
      Module attribué à <strong>{{ $route.meta.owner }}</strong> (branche
      <code>{{ $route.meta.branch }}</code>).
    </p>
    <p class="muted">
      Cet écran sera complété lors de l'intégration de la branche dédiée dans <code>dev</code>.
    </p>
    <router-link to="/" class="btn btn-secondary">Retour à l'accueil</router-link>
  </section>
</template>

<style scoped>
.muted {
  color: var(--muted);
}
</style>
