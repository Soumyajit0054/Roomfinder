import React from "react";
import { ActivityIndicator, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { BottomTabNavigationOptions, createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import MenuButton, { MenuItem } from "./src/MenuButton";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AuthProvider, useAuth } from "./src/auth";
import { Brand, colors, headerOptions } from "./src/ui";
import { LoginScreen, RegisterScreen } from "./src/screens/AuthScreens";
import BrowseScreen from "./src/screens/BrowseScreen";
import DashboardScreen from "./src/screens/DashboardScreen";
import PropertyScreen from "./src/screens/PropertyScreen";
import { FavoritesScreen, ProfileScreen, RequestsScreen } from "./src/screens/TenantScreens";
import { OwnerDashboardScreen, OwnerPropertiesScreen, OwnerRequestsScreen, PropertyFormScreen } from "./src/screens/OwnerScreens";
import { AdminDashboardScreen, AdminPropertiesScreen, AdminRequestsScreen, AdminUsersScreen } from "./src/screens/AdminScreens";

const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();

const MENUS: Record<string, MenuItem[]> = {
  tenant: [
    { name: "Dashboard", title: "Home", icon: "house" },
    { name: "Browse", title: "Find Rooms", icon: "search" },
    { name: "Favorites", title: "Favorites", icon: "heart" },
    { name: "Requests", title: "My Requests", icon: "send" },
    { name: "Profile", title: "Profile", icon: "person" },
  ],
  owner: [
    { name: "OwnerDashboard", title: "Dashboard", icon: "speedometer2" },
    { name: "OwnerProperties", title: "My Properties", icon: "houses" },
    { name: "OwnerRequests", title: "Requests", icon: "send" },
    { name: "Profile", title: "Profile", icon: "person" },
  ],
  admin: [
    { name: "AdminDashboard", title: "Overview", icon: "speedometer2" },
    { name: "AdminUsers", title: "Users", icon: "people" },
    { name: "AdminProperties", title: "Properties", icon: "houses" },
    { name: "AdminRequests", title: "Requests", icon: "send" },
    { name: "Profile", title: "Profile", icon: "person" },
  ],
};

const SCREENS: Record<string, Record<string, React.ComponentType<any>>> = {
  tenant: { Dashboard: DashboardScreen, Browse: BrowseScreen, Favorites: FavoritesScreen, Requests: RequestsScreen, Profile: ProfileScreen },
  owner: { OwnerDashboard: OwnerDashboardScreen, OwnerProperties: OwnerPropertiesScreen, OwnerRequests: OwnerRequestsScreen, Profile: ProfileScreen },
  admin: { AdminDashboard: AdminDashboardScreen, AdminUsers: AdminUsersScreen, AdminProperties: AdminPropertiesScreen, AdminRequests: AdminRequestsScreen, Profile: ProfileScreen },
};

/** One navigator per role. The bottom tab bar is hidden; navigation is the header's hamburger menu. */
function MainTabs() {
  const { user } = useAuth();
  const role = user?.role && MENUS[user.role] ? user.role : "tenant";
  const items = MENUS[role];

  return (
    <Tabs.Navigator
      key={role}
      screenOptions={({ navigation, route }) => ({
        ...headerOptions,
        headerTitle: () => <Brand />,
        headerTitleAlign: "left",
        headerRight: () => <MenuButton items={items} active={route.name} onNavigate={(n) => navigation.navigate(n)} />,
        tabBarStyle: { display: "none" },
        sceneStyle: { backgroundColor: colors.bg },
      } as BottomTabNavigationOptions)}
    >
      {items.map((it) => (
        <Tabs.Screen key={it.name} name={it.name} component={SCREENS[role][it.name]} options={{ title: it.title }} />
      ))}
    </Tabs.Navigator>
  );
}

function Root() {
  const { user, loading } = useAuth();
  if (loading) {
    return <View style={{ flex: 1, justifyContent: "center" }}><ActivityIndicator size="large" color={colors.primary} /></View>;
  }
  return (
    <Stack.Navigator screenOptions={{ ...headerOptions, contentStyle: { backgroundColor: colors.bg } }}>
      {user ? (
        <>
          <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
          <Stack.Screen name="Property" component={PropertyScreen} options={{ title: "Room details" }} />
          <Stack.Screen name="PropertyForm" component={PropertyFormScreen} />
        </>
      ) : (
        <>
          <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
          <Stack.Screen name="Register" component={RegisterScreen} options={{ title: "Create account" }} />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <NavigationContainer>
          <Root />
        </NavigationContainer>
        <StatusBar style="light" />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
