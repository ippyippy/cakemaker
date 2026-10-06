import SwiftUI

struct DriveModeView: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.dismiss) private var dismiss
    let ranked: RankedStation

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(red: 0.08, green: 0.12, blue: 0.10), Color.black],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            ScrollView {
                VStack(spacing: 0) {
                    header

                    DashMascotView(height: 265, cornerRadius: 0)
                        .background(Color.fillMeGreen.opacity(0.08))

                    VStack(alignment: .leading, spacing: 14) {
                        Text("BEST PRICE")
                            .font(.caption.weight(.black))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 7)
                            .background(Color.fillMeGreen)
                            .clipShape(RoundedRectangle(cornerRadius: 9))

                        HStack(alignment: .firstTextBaseline, spacing: 5) {
                            Text(String(format: "%.1f", ranked.station.price ?? 0))
                                .font(.system(size: 82, weight: .black, design: .rounded))
                                .tracking(-5)
                            Text("¢/L")
                                .font(.system(size: 24, weight: .bold))
                                .foregroundStyle(.white.opacity(0.75))
                        }
                        .foregroundStyle(.white)

                        HStack(spacing: 12) {
                            StationLogoView(station: ranked.station, size: 50)

                            VStack(alignment: .leading, spacing: 3) {
                                Text(ranked.station.station_name)
                                    .font(.system(size: 28, weight: .black, design: .rounded))
                                    .foregroundStyle(.white)

                                Text(ranked.station.address ?? ranked.station.suburb ?? "")
                                    .font(.subheadline)
                                    .foregroundStyle(.white.opacity(0.62))
                            }
                        }

                        HStack(spacing: 20) {
                            Label(String(format: "%.1f km", ranked.distanceKm), systemImage: "mappin.circle.fill")
                            Label("~\(ranked.etaMinutes) min", systemImage: "clock.fill")
                        }
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(.white.opacity(0.82))

                        Divider().overlay(.white.opacity(0.18))

                        HStack(spacing: 14) {
                            Image(systemName: "dollarsign.circle.fill")
                                .font(.system(size: 52))
                                .foregroundStyle(Color.fillMeGreen)
                            VStack(alignment: .leading, spacing: 1) {
                                Text("You’ll save about")
                                    .font(.subheadline)
                                    .foregroundStyle(.white.opacity(0.72))
                                Text(ranked.saving, format: .currency(code: "AUD"))
                                    .font(.system(size: 31, weight: .black, design: .rounded))
                                    .foregroundStyle(Color.fillMeGreen)
                            }
                        }

                        Button {
                            model.openInAppleMaps(ranked.station)
                        } label: {
                            HStack {
                                Image(systemName: "location.fill")
                                Text("GO")
                                    .font(.system(size: 25, weight: .black))
                                Spacer()
                                Image(systemName: "chevron.right")
                            }
                            .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.fillMeGreen)
                        .foregroundStyle(.white)
                        .controlSize(.large)
                    }
                    .padding(20)
                }
            }
        }
        .preferredColorScheme(.dark)
    }

    private var header: some View {
        HStack {
            Button {
                dismiss()
            } label: {
                Image(systemName: "chevron.left")
                    .font(.title3.weight(.bold))
                    .foregroundStyle(.white)
                    .frame(width: 42, height: 42)
            }

            Spacer()

            Text("Drive Mode")
                .font(.title2.weight(.black))
                .foregroundStyle(.white)

            Spacer()

            Color.clear.frame(width: 42, height: 42)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 8)
    }
}
