import SwiftUI

struct AlertsView: View {
    @AppStorage("nativeAlertFrequency") private var frequency = "daily"
    @AppStorage("nativeAlertRadius") private var alertRadius = 10.0
    @State private var savedFlash = false

    private let options: [(String, String, String)] = [
        ("daily", "Daily", "Once per day with the best prices"),
        ("weekdays", "Weekdays", "Monday – Friday only"),
        ("twice_daily", "Twice daily", "Morning and evening"),
        ("price_drop_only", "Price-drop only", "Only flag a drop when refreshed prices are lower"),
        ("off", "Off", "Turn off alert preferences")
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Price Alerts")
                    .font(.system(size: 31, weight: .black, design: .rounded))
                    .tracking(-1.2)
                    .foregroundStyle(Color.fillMeInk)
                    .padding(.top, 10)

                hero

                Text("Notification Frequency")
                    .font(.title3.weight(.black))
                    .foregroundStyle(Color.fillMeInk)

                VStack(spacing: 0) {
                    ForEach(options, id: \.0) { option in
                        Button {
                            withAnimation(.easeInOut(duration: 0.15)) {
                                frequency = option.0
                            }
                        } label: {
                            HStack(spacing: 14) {
                                ZStack {
                                    Circle()
                                        .stroke(frequency == option.0 ? Color.fillMeGreen : Color.secondary.opacity(0.72), lineWidth: 2)
                                        .frame(width: 28, height: 28)
                                    if frequency == option.0 {
                                        Circle()
                                            .fill(Color.fillMeGreen)
                                            .frame(width: 16, height: 16)
                                    }
                                }

                                VStack(alignment: .leading, spacing: 3) {
                                    Text(option.1)
                                        .font(.headline.weight(.black))
                                        .foregroundStyle(Color.fillMeInk)
                                    Text(option.2)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                        .fixedSize(horizontal: false, vertical: true)
                                }

                                Spacer()
                            }
                            .padding(.horizontal, 14)
                            .frame(minHeight: 72)
                            .background(frequency == option.0 ? Color.fillMeGreen.opacity(0.07) : Color.white)
                        }
                        .buttonStyle(.plain)

                        if option.0 != options.last?.0 {
                            Divider().padding(.leading, 56)
                        }
                    }
                }
                .overlay(RoundedRectangle(cornerRadius: 20).stroke(Color.black.opacity(0.07)))
                .clipShape(RoundedRectangle(cornerRadius: 20))

                VStack(spacing: 13) {
                    HStack {
                        Label("Alert Radius", systemImage: "bell.fill")
                            .font(.headline.weight(.black))
                        Spacer()
                        Text("\(Int(alertRadius)) km")
                            .font(.headline.weight(.black))
                    }

                    Slider(value: $alertRadius, in: 5...50, step: 5)
                        .tint(.fillMeGreen)

                    HStack {
                        Text("5 km")
                        Spacer()
                        Text("10 km")
                        Spacer()
                        Text("25 km")
                        Spacer()
                        Text("50 km")
                    }
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.secondary)
                }
                .padding(18)
                .background(Color.white)
                .overlay(RoundedRectangle(cornerRadius: 20).stroke(Color.black.opacity(0.07)))
                .clipShape(RoundedRectangle(cornerRadius: 20))

                Button {
                    savedFlash = true
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                        savedFlash = false
                    }
                } label: {
                    HStack {
                        Image(systemName: savedFlash ? "checkmark.circle.fill" : "bell.badge.fill")
                        Text(savedFlash ? "Preferences Saved" : "Save Alert Preferences")
                        Spacer()
                    }
                    .font(.headline.weight(.black))
                    .frame(maxWidth: .infinity)
                    .frame(height: 54)
                    .padding(.horizontal, 16)
                }
                .buttonStyle(.plain)
                .foregroundStyle(.white)
                .background(Color.fillMeGreen)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))

                Text("These preferences are stored on this device. FillMeNow does not claim a price notification was delivered unless iOS has actually delivered one.")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 4)
            }
            .padding(.horizontal, 18)
            .padding(.bottom, 30)
        }
        .background(Color.white.ignoresSafeArea())
        .navigationBarHidden(true)
    }

    private var hero: some View {
        HStack(spacing: 8) {
            ZStack(alignment: .bottomTrailing) {
                DashMascotView(height: 178, cornerRadius: 24)
                    .frame(width: 168)
                Image(systemName: "bell.fill")
                    .font(.system(size: 30, weight: .black))
                    .foregroundStyle(.white)
                    .padding(10)
                    .background(Color.fillMeGreen)
                    .clipShape(Circle())
                    .offset(x: -3, y: -3)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("I’ll watch\nthe prices\nfor you!")
                    .font(.system(size: 25, weight: .black, design: .rounded))
                    .tracking(-0.9)
                    .foregroundStyle(Color.fillMeInk)

                Text("Set how often and how far you want FillMeNow to check.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity)
    }
}
