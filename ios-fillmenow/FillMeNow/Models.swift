import Foundation
import CoreLocation

struct PriceResponse: Decodable {
    let ok: Bool
    let rows: [FuelStation]
    let price_date: String?
    let snapshot_synced_at: String?
}

struct FuelStation: Codable, Identifiable, Hashable {
    let station_id: String
    let station_name: String
    let brand: String?
    let suburb: String?
    let address: String
    let postcode: String?
    let latitude: Double
    let longitude: Double
    let price: Double?
    let fuel_type: String?
    let price_date: String?

    var id: String { station_id }
    var coordinate: CLLocationCoordinate2D { .init(latitude: latitude, longitude: longitude) }
}

struct RankedStation: Identifiable {
    let station: FuelStation
    let distanceKm: Double
    let roadKm: Double
    let etaMinutes: Int
    let effectivePrice: Double
    let saving: Double

    var id: String { station.id }
}

enum FuelState: String, CaseIterable, Identifiable {
    case NSW, WA, TAS
    var id: String { rawValue }

    var name: String {
        switch self {
        case .NSW: return "New South Wales"
        case .WA: return "Western Australia"
        case .TAS: return "Tasmania"
        }
    }

    var fuels: [String] {
        switch self {
        case .NSW, .TAS: return ["Diesel", "U91", "E10", "U95", "U98"]
        case .WA: return ["Diesel", "U91", "U95", "U98"]
        }
    }
}

enum VehiclePreset: String, CaseIterable, Identifiable {
    case car, ute, truck, heavy, custom
    var id: String { rawValue }

    var title: String {
        switch self {
        case .car: return "Car"
        case .ute: return "Ute / Van"
        case .truck: return "Truck"
        case .heavy: return "Heavy Truck"
        case .custom: return "Custom"
        }
    }

    var defaults: (tank: Double, economy: Double)? {
        switch self {
        case .car: return (65, 9)
        case .ute: return (120, 14)
        case .truck: return (600, 35)
        case .heavy: return (1000, 45)
        case .custom: return nil
        }
    }
}
