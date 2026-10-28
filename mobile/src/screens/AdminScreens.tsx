import React, { useCallback, useState } from "react";
import { ActivityIndicator, Alert, FlatList, RefreshControl, ScrollView, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { AdminRequest, AdminUser, api, Property } from "../api";
import { useAuth } from "../auth";
import { confirm, errorMessage, useList } from "../hooks";
import { Button, colors, Empty, ErrorText, Eyebrow, Pill, Row, StatCard, StatusBadge } from "../ui";

export function AdminDashboardScreen() {
  const [stats, setStats] = useState<Awaited<ReturnType<typeof api.adminDashboard>> | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useFocusEffect(useCallback(() => {
    api.adminDashboard().then(setStats).catch((e) => setErr(errorMessage(e, "Could not load.")));
  }, []));

  return (
    <ScrollView style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}>
      <Eyebrow>Admin dashboard</Eyebrow>
      <Text style={{ fontSize: 28, fontWeight: "800", color: colors.text, marginBottom: 16 }}>Platform overview</Text>
      <ErrorText>{err}</ErrorText>
      {!stats && !err && <ActivityIndicator color={colors.primary} />}
      {stats && (
        <View style={{ gap: 12 }}>
          <StatCard label="Total Users" value={stats.users} icon="people" tone="blue" />
          <StatCard label="Tenants" value={stats.tenants} icon="person" tone="green" />
          <StatCard label="Owners" value={stats.owners} icon="house-heart" tone="gold" />
          <StatCard label="Properties" value={stats.properties} icon="houses" tone="blue" />
          <StatCard label="Rental Requests" value={stats.requests} icon="send" tone="red" />
        </View>
      )}
    </ScrollView>
  );
}

const fetchUsers = () => api.adminUsers().then((r) => r.users);

export function AdminUsersScreen() {
  const { user: me } = useAuth();
  const { items, loading, err, load } = useList<AdminUser>(fetchUsers);

  const remove = (u: AdminUser) =>
    confirm("Delete user", `Delete ${u.name} (${u.email})? Their properties and requests will be deleted too.`, "Delete", async () => {
      try { await api.adminDeleteUser(u.id); load(); }
      catch (e) { Alert.alert("Error", errorMessage(e)); }
    });

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  return (
    <FlatList
      style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}
      data={items} keyExtractor={(u) => String(u.id)}
      refreshControl={<RefreshControl refreshing={false} onRefresh={load} />}
      ListHeaderComponent={<ErrorText>{err}</ErrorText>}
      ListEmptyComponent={<Empty icon="people" text="No users." />}
      renderItem={({ item: u }) => (
        <Row>
          <Text style={{ fontWeight: "700", fontSize: 16 }}>{u.name}</Text>
          <Text style={{ color: colors.muted }}>{u.email}{u.phone ? ` · ${u.phone}` : ""}</Text>
          <View style={{ marginTop: 6 }}><Pill label={u.role} /></View>
          {u.id !== me?.id && <View style={{ marginTop: 10 }}><Button title="Delete user" icon="trash3" variant="outline" onPress={() => remove(u)} /></View>}
        </Row>
      )}
    />
  );
}

const fetchProps = () => api.adminProperties().then((r) => r.properties);

export function AdminPropertiesScreen({ navigation }: any) {
  const { items, loading, err, load } = useList<Property>(fetchProps);

  const remove = (p: Property) =>
    confirm("Delete property", `Delete "${p.title}"? This cannot be undone.`, "Delete", async () => {
      try { await api.adminDeleteProperty(p.id); load(); }
      catch (e) { Alert.alert("Error", errorMessage(e)); }
    });

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  return (
    <FlatList
      style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}
      data={items} keyExtractor={(p) => String(p.id)}
      refreshControl={<RefreshControl refreshing={false} onRefresh={load} />}
      ListHeaderComponent={<ErrorText>{err}</ErrorText>}
      ListEmptyComponent={<Empty text="No properties." />}
      renderItem={({ item: p }) => (
        <Row>
          <Text style={{ fontWeight: "700", fontSize: 16 }} onPress={() => navigation.navigate("Property", { id: p.id })}>{p.title}</Text>
          <Text style={{ color: colors.muted }}>{p.location} · {p.rent.toLocaleString()} / month</Text>
          <Text style={{ color: colors.muted }}>Owner: {p.owner_name} · {p.available ? "Available" : "Taken"}</Text>
          <View style={{ marginTop: 10 }}><Button title="Delete property" icon="trash3" variant="outline" onPress={() => remove(p)} /></View>
        </Row>
      )}
    />
  );
}

const fetchReqs = () => api.adminRequests().then((r) => r.requests);

export function AdminRequestsScreen() {
  const { items, loading, err, load } = useList<AdminRequest>(fetchReqs);
  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={colors.primary} />;
  return (
    <FlatList
      style={{ backgroundColor: colors.bg }} contentContainerStyle={{ padding: 16 }}
      data={items} keyExtractor={(r) => String(r.id)}
      refreshControl={<RefreshControl refreshing={false} onRefresh={load} />}
      ListHeaderComponent={<ErrorText>{err}</ErrorText>}
      ListEmptyComponent={<Empty icon="send" text="No rental requests." />}
      renderItem={({ item: r }) => (
        <Row>
          <Text style={{ fontWeight: "700", fontSize: 16 }}>{r.property.title}</Text>
          <Text style={{ color: colors.muted }}>{r.property.location} · {r.property.rent.toLocaleString()} / month</Text>
          <Text style={{ marginTop: 4 }}>Tenant: {r.tenant_name}</Text>
          <Text>Owner: {r.owner_name}</Text>
          <View style={{ marginTop: 6 }}><StatusBadge status={r.status} /></View>
        </Row>
      )}
    />
  );
}
