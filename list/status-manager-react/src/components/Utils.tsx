export function rgbToHex(rgb: string) {
    const rgbArray = rgb.match(/\d+/g)!;
    return "#" + rgbArray.map(x => {
        const hex = parseInt(x).toString(16);
        return hex.length === 1 ? "0" + hex : hex;
    }).join('');
}