import React, { useEffect, useState } from "react";
import { ActivityIndicator, FlatList, RefreshControl, ScrollView, Text, View } from "react-native";
import { api, Profile, Property, RentalRequest } from "../api";
import { useList } from "../hooks";
import { useAuth } from "../auth";
import Icon from "../Icon";
import { Button, colors, Empty, ErrorText, IconTile, PropertyCard, Row, SectionHeader, StatusBadge } from "../ui";

const fetchFavs = () => api.favorites().then((r) => r.properties);
const fetchReqs = () => api.requests().then((r) => r.requests);

export function FavoritesScreen({ navigation }: any) {
  const { items, loading, err, load } = useList<Property>(fetchFavs);
  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  return (
    <FlatList
      style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}
      data={items} keyExtractor={(p) => String(p.id)}
      refreshControl={<RefreshControl refreshing={false} onRefresh={load} />}
      ListHeaderComponent={<ErrorText>{err}</ErrorText>}
      ListEmptyComponent={<Empty icon="heart" text="No favorites yet. Save a room from its details page." />}
      renderItem={({ item }) => <PropertyCard item={item} onPress={() => navigation.navigate("Property", { id: item.id })} />}
    />
  );
}

export function RequestsScreen({ navigation }: any) {
  const { items, loading, err, load } = useList<RentalRequest>(fetchReqs);
  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  return (
    <FlatList
      style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}
      data={items} keyExtractor={(r) => String(r.id)}
      refreshControl={<RefreshControl refreshing={false} onRefresh={load} />}
      ListHeaderComponent={<ErrorText>{err}</ErrorText>}
      ListEmptyComponent={<Empty icon="send" text="You haven't sent any requests." />}
      renderItem={({ item: r }) => (
        <Row>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
            <Text style={{ fontWeight: "800", fontSize: 16, flex: 1 }} onPress={() => navigation.navigate("Property", { id: r.property.id })}>{r.property.title}</Text>
            <StatusBadge status={r.status} />
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 6 }}>
            <Icon name="geo-alt" size={14} color={colors.primary} />
            <Text style={{ color: colors.muted }}>{r.property.location} · ₹{r.property.rent.toLocaleString()} / month</Text>
          </View>
          {!!r.message && <Text style={{ marginTop: 8, fontStyle: "italic", color: colors.text }}>"{r.message}"</Text>}
          {!!r.created_at && <Text style={{ marginTop: 8, color: colors.muted, fontSize: 12 }}>Sent {new Date(r.created_at).toLocaleDateString()}</Text>}
        </Row>
      )}
    />
  );
}

export function ProfileScreen() {
  const { user, signOut } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  useEffect(() => { api.profile().then((r) => setProfile(r.profile)).catch(() => {}); }, []);

  const verified = profile?.id_verified;
  const row = (icon: any, k: string, v?: string | null) => v ? (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 12, borderBottomWidth: 1, borderColor: colors.border }}>
      <IconTile name={icon} size={38} />
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.muted, fontSize: 12 }}>{k}</Text>
        <Text style={{ fontWeight: "600", color: colors.text, textTransform: k === "ID verification" ? "capitalize" : "none" }}>{v}</Text>
      </View>
    </View>
  ) : null;

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}>
      <Row style={{ alignItems: "center", paddingVertical: 24 }}>
        <View style={{ width: 76, height: 76, borderRadius: 38, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
          <Icon name="person-fill" size={38} color="#fff" />
        </View>
        <Text style={{ fontSize: 22, fontWeight: "800", color: colors.text }}>{user?.name}</Text>
        <Text style={{ color: colors.primary, fontWeight: "700", textTransform: "capitalize", marginTop: 2 }}>{user?.role}</Text>
        {verified && (
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginTop: 8 }}>
            <Icon name="patch-check-fill" size={15} color={colors.success} />
            <Text style={{ color: colors.success, fontWeight: "600", fontSize: 13 }}>ID verified</Text>
          </View>
        )}
      </Row>
      <Row style={{ paddingVertical: 4 }}>
        {row("envelope", "Email", profile?.email ?? user?.email)}
        {row("telephone", "Phone", profile?.phone)}
        {row("geo-alt", "Country", profile?.country)}
        {row("person-vcard", "ID verification", profile?.id_status ? profile.id_status.replace("_", " ") : null)}
        {row("calendar3", "Member since", profile?.member_since ? new Date(profile.member_since).toLocaleDateString() : null)}
      </Row>
      <View style={{ height: 8 }} />
      <Button title="Log out" icon="box-arrow-right" variant="outline" onPress={signOut} />
    </ScrollView>
  );
}
