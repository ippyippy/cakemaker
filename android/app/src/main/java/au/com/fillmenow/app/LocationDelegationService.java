package au.com.fillmenow.app;

import android.os.Bundle;
import com.google.androidbrowserhelper.trusted.DelegationService;
import com.google.androidbrowserhelper.locationdelegation.LocationDelegationExtraCommandHandler;

/**
 * Official Android Browser Helper protocol. DelegationService verifies the calling browser
 * against its registered token store; do not replace this with an unverified JS/Binder bridge.
 * Native positions flow to the existing navigator.geolocation watch in the verified TWA.
 */
public final class LocationDelegationService extends DelegationService {
    private final LocationDelegationExtraCommandHandler location = new LocationDelegationExtraCommandHandler();
    public LocationDelegationService() { registerExtraCommandHandler(location); }
    @Override public void onDestroy() {
        location.handleExtraCommand(this, "stopLocation", Bundle.EMPTY, null);
        super.onDestroy();
    }
}
