import React, { useCallback, useState } from "react";
import { ActivityIndicator, RefreshControl, ScrollView, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { api, Property } from "../api";
import { useAuth } from "../auth";
import { errorMessage } from "../hooks";
import { Button, colors, Empty, ErrorText, Eyebrow, PropertyCard, SectionHeader, StatCard, Row, IconTile } from "../ui";

/** Tenant home: mirrors the web "Tenant Dashboard" (greeting, stat cards, recommended rooms). */
export default function DashboardScreen({ navigation }: any) {
  const { user } = useAuth();
  const [rooms, setRooms] = useState<Property[] | null>(null);
  const [saved, setSaved] = useState<number | null>(null);
  const [requests, setRequests] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [p, f, r] = await Promise.all([api.properties({ limit: 8 }), api.favorites(), api.requests()]);
      setRooms(p.properties); setSaved(f.properties.length); setRequests(r.requests.length); setErr(null);
    } catch (e) { setErr(errorMessage(e, "Could not load your dashboard.")); }
    finally { setRefreshing(false); }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const goBrowse = () => navigation.navigate("Browse");

  return (
    <ScrollView
      style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
    >
      <Eyebrow>Tenant dashboard</Eyebrow>
      <Text style={{ fontSize: 30, fontWeight: "800", color: colors.text, marginTop: 2 }}>Hello, {user?.name} 👋</Text>
      <Text style={{ color: colors.muted, marginTop: 4, marginBottom: 16 }}>Discover comfortable rooms and find a place that feels like home.</Text>
      <Button title="Find a Room" icon="search" onPress={goBrowse} />

      <View style={{ gap: 12, marginTop: 20 }}>
        <StatCard label="Available Rooms" value={rooms ? rooms.length : "—"} icon="house" tone="blue" />
        <StatCard label="Saved Rooms" value={saved ?? "—"} icon="heart" tone="red" />
        <StatCard label="Rental Requests" value={requests ?? "—"} icon="send" tone="gold" />
      </View>

      <Row style={{ marginTop: 16, flexDirection: "row", alignItems: "center", gap: 12, backgroundColor: "#f7fafd" }}>
        <IconTile name="search" bg="#fff" />
        <View style={{ flex: 1 }}>
          <Text style={{ fontWeight: "800", fontSize: 16 }}>Looking for a room?</Text>
          <Text style={{ color: colors.muted, fontSize: 13 }}>Search by location, budget and room preference.</Text>
        </View>
      </Row>
      <Button title="Explore Rooms" variant="outline" icon="arrow-right" onPress={goBrowse} />

      <View style={{ marginTop: 28 }}>
        <SectionHeader eyebrow="Recommended for you" title="Available Rooms" subtitle="Rooms currently available on RoomFinder."
          action="View all" onAction={goBrowse} />
        <ErrorText>{err}</ErrorText>
        {!rooms && !err && <ActivityIndicator color={colors.primary} style={{ marginTop: 20 }} />}
        {rooms?.length === 0 && <Empty text="No rooms are available right now. Check back soon." />}
        {rooms?.map((p) => <PropertyCard key={p.id} item={p} onPress={() => navigation.navigate("Property", { id: p.id })} />)}
      </View>
    </ScrollView>
  );
}
