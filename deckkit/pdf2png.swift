// Rasterise every page of a PDF to PNG with macOS's own PDFKit -- nothing to install.
//     swift deckkit/pdf2png.swift <in.pdf> <outdir> [width-px]
// Writes slide-01.png, slide-02.png, ... and prints the page count. Used by
// deckkit/snapshot.py after PowerPoint exports the deck as PDF.
import AppKit
import PDFKit
let a = CommandLine.arguments
guard a.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("usage: pdf2png <in.pdf> <outdir> [width]\n".data(using: .utf8)!); exit(2) }
let out = URL(fileURLWithPath: a[2]); let width = Double(a.count > 3 ? a[3] : "1600") ?? 1600
try? FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
for i in 0..<doc.pageCount {
    let page = doc.page(at: i)!, box = page.bounds(for: .mediaBox), k = width / box.width
    let image = page.thumbnail(of: NSSize(width: box.width * k, height: box.height * k), for: .mediaBox)
    guard let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
          let png = rep.representation(using: .png, properties: [:]) else { exit(1) }
    try! png.write(to: out.appendingPathComponent(String(format: "slide-%02d.png", i + 1)))
}
print(doc.pageCount)
