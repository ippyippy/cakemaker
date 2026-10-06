import SwiftUI

struct OnboardingView: View {
    let onDone: () -> Void
    @State private var page = 0

    var body: some View {
        ZStack {
            Color.white.ignoresSafeArea()

            VStack(spacing: 0) {
                HStack {
                    Spacer()
                    Button("Skip") { onDone() }
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(Color.fillMeInk)
                }
                .padding(.horizontal, 22)
                .padding(.top, 8)

                TabView(selection: $page) {
                    savingsPage.tag(0)
                    bestStopPage.tag(1)
                    alertsPage.tag(2)
                }
                .tabViewStyle(.page(indexDisplayMode: .never))

                HStack(spacing: 9) {
                    ForEach(0..<3, id: \.self) { index in
                        Circle()
                            .fill(index == page ? Color.fillMeGreen : Color.black.opacity(0.13))
                            .frame(width: 10, height: 10)
                    }
                }
                .padding(.bottom, 20)

                Button {
                    if page < 2 {
                        withAnimation(.easeInOut) { page += 1 }
                    } else {
                        onDone()
                    }
                } label: {
                    HStack {
                        Spacer()
                        Text(page == 2 ? "Start Exploring" : "Get Started")
                            .font(.system(size: 20, weight: .black, design: .rounded))
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.title3.weight(.black))
                    }
                    .padding(.horizontal, 20)
                    .frame(height: 64)
                }
                .buttonStyle(.plain)
                .foregroundStyle(.white)
                .background(Color.fillMeInk)
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                .padding(.horizontal, 20)
                .padding(.bottom, 14)
            }
        }
    }

    private var savingsPage: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("You save.")
                .foregroundStyle(Color.fillMeInk)
            + Text("\nWe all win.")
                .foregroundStyle(Color.fillMeGreen)
        }
        .font(.system(size: 48, weight: .black, design: .rounded))
        .tracking(-2.3)
        .padding(.horizontal, 24)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(alignment: .bottom) {
            VStack(spacing: 4) {
                DashMascotView(height: 330, cornerRadius: 0)
                    .padding(.horizontal, 18)

                VStack(spacing: 5) {
                    Text("Find the stop worth taking")
                        .font(.headline.weight(.black))
                        .foregroundStyle(Color.fillMeInk)
                    Text("Compare live Australian fuel prices, distance and trip cost — not just the number on the sign.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 28)
                }
                .padding(.vertical, 14)
                .frame(maxWidth: .infinity)
                .background(Color.fillMeGreen.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                .padding(.horizontal, 20)
            }
        }
        .padding(.bottom, 26)
    }

    private var bestStopPage: some View {
        VStack(spacing: 20) {
            DashMascotView(height: 360, cornerRadius: 28)

            Text("Best Stop does the maths")
                .font(.system(size: 34, weight: .black, design: .rounded))
                .tracking(-1.4)
                .foregroundStyle(Color.fillMeInk)
                .multilineTextAlignment(.center)

            Text("FillMeNow weighs price, distance and your vehicle so a cheaper pump does not cost you more to reach.")
                .font(.title3)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
        }
        .padding(.horizontal, 18)
    }

    private var alertsPage: some View {
        VStack(spacing: 18) {
            ZStack(alignment: .bottomTrailing) {
                DashMascotView(height: 340, cornerRadius: 28)
                Image(systemName: "bell.fill")
                    .font(.system(size: 78, weight: .black))
                    .foregroundStyle(.white)
                    .padding(24)
                    .background(Color.fillMeGreen)
                    .clipShape(Circle())
                    .shadow(color: .black.opacity(0.15), radius: 16, y: 8)
                    .offset(x: -8, y: -8)
            }

            Text("Keep an eye on prices")
                .font(.system(size: 34, weight: .black, design: .rounded))
                .foregroundStyle(Color.fillMeInk)

            Text("Choose your alert preference and radius. FillMeNow keeps your settings ready for the price checks you want.")
                .font(.title3)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
        }
        .padding(.horizontal, 18)
    }
}
