<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'

const props = defineProps({
  title: { type: String, default: '' },
  unit: { type: String, default: '' },
  seriesName: { type: String, default: '值' },
  points: { type: Array, default: () => [] }, // [{timestamp,value}]
})

const option = computed(() => {
  const times = props.points.map((p) => (p?.timestamp ? new Date(p.timestamp).toLocaleString() : ''))
  const values = props.points.map((p) => p?.value)
  return {
    title: props.title ? { text: props.title, left: 'center' } : undefined,
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: props.title ? 50 : 25, bottom: 40 },
    xAxis: { type: 'category', data: times, axisLabel: { hideOverlap: true } },
    yAxis: { type: 'value', name: props.unit || '' },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16 }],
    series: [
      {
        name: props.seriesName,
        type: 'line',
        showSymbol: false,
        smooth: true,
        data: values,
      },
    ],
  }
})
</script>

<template>
  <VChart class="chart" :option="option" autoresize />
</template>

<style scoped>
.chart {
  height: 320px;
  width: 100%;
}
</style>

