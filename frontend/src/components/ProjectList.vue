<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type Project } from '../api'

const emit = defineEmits<{ open: [string] }>()

const projects = ref<Project[]>([])
const newName = ref('')
const newDescription = ref('')
const error = ref<string | null>(null)

async function refresh() {
  try {
    projects.value = await api.listProjects()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function createProject() {
  if (!newName.value.trim()) return
  try {
    await api.createProject({ name: newName.value, description: newDescription.value })
    newName.value = ''
    newDescription.value = ''
    await refresh()
  } catch (e) {
    error.value = (e as Error).message
  }
}

async function removeProject(id: string) {
  try {
    await api.deleteProject(id)
    await refresh()
  } catch (e) {
    error.value = (e as Error).message
  }
}

onMounted(refresh)
</script>

<template>
  <section>
    <h2>Projetos</h2>

    <form @submit.prevent="createProject">
      <input v-model="newName" placeholder="nome do projeto" required />
      <input v-model="newDescription" placeholder="descrição (opcional)" />
      <button type="submit">criar</button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>

    <ul v-if="projects.length">
      <li v-for="p in projects" :key="p.id">
        <div>
          <strong>{{ p.name }}</strong>
          <small v-if="p.description"> — {{ p.description }}</small>
        </div>
        <div class="row-actions">
          <button type="button" @click="emit('open', p.id)">abrir</button>
          <button type="button" @click="removeProject(p.id)">remover</button>
        </div>
      </li>
    </ul>
    <p v-else class="empty">nenhum projeto ainda</p>
  </section>
</template>

<style scoped>
form { display: flex; gap: 0.5rem; margin: 1rem 0; }
input { flex: 1; padding: 0.5rem; font: inherit; }
button { padding: 0.5rem 1rem; font: inherit; cursor: pointer; }
ul { list-style: none; padding: 0; }
li { display: flex; justify-content: space-between; align-items: center;
     padding: 0.75rem; border: 1px solid #8884; border-radius: 6px; margin-bottom: 0.5rem; }
.row-actions { display: flex; gap: 0.5rem; }
.empty { opacity: 0.6; font-style: italic; }
.error { color: #c33; }
</style>
