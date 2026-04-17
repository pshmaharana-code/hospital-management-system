<script setup>
import { ref } from 'vue'
import { Cropper } from 'vue-advanced-cropper';
import 'vue-advanced-cropper/dist/style.css'

const props = defineProps({
    show: Boolean,
    imageSource: String,
    isUploading: Boolean
})

const emit = defineEmits(['close', 'crop'])

const cropperRef = ref(null)

const confirmCrop = () => {
    if (!cropperRef.value) return

    const { canvas } = cropperRef.value.getResult()
    if (!canvas) return

    canvas.toBlob((blob) => {
        emit('crop', blob)
    }, 'image/jepg', 0.9)
}
</script>

<template>
    <div v-if="show" class="modal-overlay">
        <div class="crop-modal-content">
            <h3>Adjust Profile Picture</h3>
            <div class="cropper-wrapper">
                <cropper 
                    ref="cropperRef" 
                    :src="imageSource" 
                    :stencil-props="{ aspectRatio: 1/1 }" 
                    class="vue-cropper"
                />
            </div>
            <div class="crop-action">
                <button @click="$emit('close')" class="btn-secondary" :disabled="isUploading">Cancel</button>
                <button @click="confirmCrop" class="btn-primary" :disabled="isUploading">
                    {{ isUploading ? 'Uploading...' : 'Crop & Save' }}
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.crop-modal-content { background: white; padding: 2rem; border-radius: 12px; width: 100%; max-width: 500px; text-align: center; }
.crop-modal-content h3 { margin-top: 0; color: #2c3e50; margin-bottom: 1.5rem;}
.cropper-wrapper { height: 350px; background: #000; margin-bottom: 1.5rem; border-radius: 8px; overflow: hidden; }
.vue-cropper { width: 100%; height: 100%; }
.crop-actions { display: flex; gap: 1rem; justify-content: flex-end; }
.btn-secondary { background: #95a5a6; color: white; padding: 0.8rem 1.5rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
.btn-primary { background: #3498db; color: white; padding: 0.8rem 1.5rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
.btn-primary:hover:not(:disabled) { background: #2980b9; }
</style>