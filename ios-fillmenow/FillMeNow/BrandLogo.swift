import SwiftUI

enum BrandLogo {
    static func key(brand: String?, name: String) -> String {
        let s = "\(brand ?? "") \(name)".lowercased()
        if s.contains("reddy") { return "reddy" }
        if s.contains("7-eleven") || s.contains("7 eleven") { return "seven" }
        if s.contains("ampol") { return "ampol" }
        if s.range(of: #"(^|\s)bp(\s|$)"#, options: .regularExpression) != nil { return "bp" }
        if s.contains("shell") { return "shell" }
        if s.contains("metro") { return "metro" }
        if s.contains("united") { return "united" }
        if s.contains("liberty") { return "liberty" }
        if s.contains("mobil") { return "mobil" }
        if s.contains("caltex") { return "caltex" }
        if s.contains("speedway") { return "speedway" }
        if s.contains("vibe") { return "vibe" }
        if s.contains("tas petroleum") { return "taspet" }
        if s.contains("u-go") || s.contains("u go") { return "ugo" }
        if s.contains("puma") { return "puma" }
        return ""
    }

    static func url(brand: String?, name: String) -> URL? {
        let urls: [String: String] = [
            "bp": "https://cdn.simpleicons.org/bp",
            "shell": "https://cdn.simpleicons.org/shell",
            "seven": "https://cdn.simpleicons.org/7eleven",
            "mobil": "https://cdn.simpleicons.org/mobil",
            "ampol": "https://www.ampol.com.au/favicon.ico",
            "reddy": "https://www.reddyexpress.com.au/favicon.ico",
            "metro": "https://www.metropetroleum.com.au/favicon.ico",
            "united": "https://www.unitedpetroleum.com.au/favicon.ico",
            "liberty": "https://libertyoil.com.au/favicon.ico",
            "caltex": "https://www.caltex.com/favicon.ico",
            "speedway": "https://speedway.com.au/favicon.ico",
            "vibe": "https://vibepetroleum.com/favicon.ico",
            "taspet": "https://taspetroleum.com.au/favicon.ico",
            "ugo": "https://www.ugoselfserve.com.au/favicon.ico",
            "puma": "https://pumaenergy.com/favicon.ico"
        ]
        guard let raw = urls[key(brand: brand, name: name)] else { return nil }
        return URL(string: raw)
    }

    static func label(brand: String?, name: String) -> String {
        let generic = ["independent", "independent retailer", "unbranded", "other", "unknown", "n/a", "na"]
        let b = (brand ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let raw = b.isEmpty || generic.contains(b.lowercased()) ? name : b
        let first = raw.split(separator: " ").first.map(String.init) ?? "FUEL"
        return String(first.uppercased().prefix(7))
    }
}

struct StationLogoView: View {
    let station: FuelStation
    var size: CGFloat = 38

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 8)
                .fill(.white)
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.black.opacity(0.08)))

            if let url = BrandLogo.url(brand: station.brand, name: station.station_name) {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image.resizable().scaledToFit().padding(3)
                    default:
                        fallback
                    }
                }
            } else {
                fallback
            }
        }
        .frame(width: size, height: size)
    }

    private var fallback: some View {
        Text(BrandLogo.label(brand: station.brand, name: station.station_name))
            .font(.system(size: max(7, size * 0.18), weight: .black))
            .foregroundStyle(Color.fillMeInk)
            .minimumScaleFactor(0.55)
            .padding(3)
    }
}
