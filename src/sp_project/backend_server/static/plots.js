function plot1() {
    const response = await fetch('/plot')
    const item = await response.json()
    Bokeh.embed.embed_item(item, "plots")
}


/*
<script type="module">
const response = await fetch('/plot')
const item = await response.json()
Bokeh.embed.embed_item(item, "plots")
</script>
*/